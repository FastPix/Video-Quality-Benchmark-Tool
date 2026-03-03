import os
import json
import argparse
import subprocess
import numpy as np
import cv2
import shutil
import tempfile
import soundfile as sf
from skimage.metrics import structural_similarity as ssim
from tqdm import tqdm
import matplotlib.pyplot as plt

TMP_SRC = "tmp_frames_src"
TMP_ENC = "tmp_frames_enc"
HEATMAP_DIR = "ssim_heatmaps"

# -----------------------------------
# Utility
# -----------------------------------
def run_cmd(cmd):
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# -----------------------------------
# VMAF + SAFE FEATURE EXTRACTION
# -----------------------------------
def compute_vmaf_full(src, enc):
    vmaf_log = "vmaf_log.json"

    cmd = [
        "ffmpeg", "-y",
        "-i", enc,
        "-i", src,
        "-lavfi",
        "libvmaf=log_path=vmaf_log.json:log_fmt=json",
        "-f", "null", "-"
    ]
    run_cmd(cmd)

    if not os.path.exists(vmaf_log):
        return {"vmaf_error": "VMAF log not generated"}

    with open(vmaf_log) as f:
        data = json.load(f)

    pooled = data.get("pooled_metrics", {})
    frames = data.get("frames", [])

    vmaf_per_frame = [
        f["metrics"]["vmaf"]
        for f in frames
        if "vmaf" in f.get("metrics", {})
    ]

    results = {
        "vmaf_average": pooled.get("vmaf", {}).get("mean"),
        "vmaf_min": float(np.min(vmaf_per_frame)) if vmaf_per_frame else None,
        "vmaf_std": float(np.std(vmaf_per_frame)) if vmaf_per_frame else None,
        "vmaf_worst_frame_index": int(np.argmin(vmaf_per_frame)) if vmaf_per_frame else None,
    }

    # Optional features (only if available in your FFmpeg build)
    optional_metrics = [
        "adm2",
        "motion",
        "vif_scale0",
        "vif_scale1",
        "vif_scale2",
        "vif_scale3"
    ]

    for metric in optional_metrics:
        if metric in pooled:
            results[metric] = pooled[metric]["mean"]

    return results

# -----------------------------------
# PSNR (Avg + Worst + Std + Index)
# -----------------------------------
def compute_psnr_full(src, enc):
    stats_file = "psnr_log.txt"

    cmd = [
        "ffmpeg", "-i", enc, "-i", src,
        "-lavfi", f"psnr=stats_file={stats_file}",
        "-f", "null", "-"
    ]
    run_cmd(cmd)

    psnr_values = []

    if not os.path.exists(stats_file):
        return {"psnr_error": "PSNR log not generated"}

    with open(stats_file) as f:
        for line in f:
            if "psnr_avg:" in line:
                val = float(line.split("psnr_avg:")[1].split()[0])
                psnr_values.append(val)

    if not psnr_values:
        return {"psnr_error": "No PSNR values found"}

    return {
        "psnr_average": float(np.mean(psnr_values)),
        "psnr_std": float(np.std(psnr_values)),
        "psnr_worst_frame": float(np.min(psnr_values)),
        "psnr_worst_frame_index": int(np.argmin(psnr_values))
    }

# -----------------------------------
# Frame Extraction
# -----------------------------------
def extract_frames(video, output_dir, prefix):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    pattern = os.path.join(output_dir, f"{prefix}_%05d.png")

    run_cmd([
        "ffmpeg", "-y", "-i", video,
        "-vsync", "0",
        pattern
    ])

    return sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir)])

# -----------------------------------
# SSIM Heatmap
# -----------------------------------
def save_ssim_heatmap(src_img, enc_img, frame_idx):
    score, ssim_map = ssim(src_img, enc_img, full=True)
    heatmap = 1 - ssim_map

    os.makedirs(HEATMAP_DIR, exist_ok=True)

    plt.figure(figsize=(6, 6))
    plt.imshow(heatmap, cmap='hot')
    plt.colorbar()
    plt.title(f"SSIM Heatmap Frame {frame_idx}")
    plt.axis("off")
    plt.savefig(os.path.join(HEATMAP_DIR, f"ssim_heatmap_{frame_idx}.png"))
    plt.close()

    return score

# -----------------------------------
# Frame-Level Metrics
# -----------------------------------
def frame_level_metrics(src_frames, enc_frames):
    ssims = []
    flicker_scores = []
    edge_ratios = []
    noise_diff = []
    motion_stability = []

    prev_mean_luma = None
    prev_frame = None

    min_len = min(len(src_frames), len(enc_frames))

    for i in tqdm(range(min_len)):
        src_img = cv2.imread(src_frames[i], 0)
        enc_img = cv2.imread(enc_frames[i], 0)

        if src_img is None or enc_img is None:
            continue

        # SSIM + heatmap
        s = save_ssim_heatmap(src_img, enc_img, i)
        ssims.append(s)

        # Motion stability
        if prev_frame is not None:
            motion_stability.append(ssim(prev_frame, enc_img))
        prev_frame = enc_img

        # Edge retention
        edge_src = cv2.Laplacian(src_img, cv2.CV_64F).var()
        edge_enc = cv2.Laplacian(enc_img, cv2.CV_64F).var()
        edge_ratios.append(edge_enc / (edge_src + 1e-6))

        # Noise preservation
        blur_src = cv2.GaussianBlur(src_img, (5, 5), 0)
        blur_enc = cv2.GaussianBlur(enc_img, (5, 5), 0)

        noise_src = src_img - blur_src
        noise_enc = enc_img - blur_enc
        noise_diff.append(np.std(noise_enc) - np.std(noise_src))

        # Flicker
        mean_luma = np.mean(enc_img)
        if prev_mean_luma is not None:
            flicker_scores.append(abs(mean_luma - prev_mean_luma))
        prev_mean_luma = mean_luma

    return {
        "avg_frame_ssim": float(np.mean(ssims)) if ssims else None,
        "min_frame_ssim": float(np.min(ssims)) if ssims else None,
        "ssim_std": float(np.std(ssims)) if ssims else None,
        "edge_retention_ratio": float(np.median(edge_ratios)) if edge_ratios else None,
        "edge_variance": float(np.std(edge_ratios)) if edge_ratios else None,
        "avg_noise_difference": float(np.mean(noise_diff)) if noise_diff else None,
        "noise_variance": float(np.std(noise_diff)) if noise_diff else None,
        "temporal_flicker_score": float(np.mean(flicker_scores)) if flicker_scores else None,
        "flicker_variance": float(np.std(flicker_scores)) if flicker_scores else None,
        "motion_stability_score": float(np.mean(motion_stability)) if motion_stability else None,
        "motion_variance": float(np.std(motion_stability)) if motion_stability else None
    }

# -----------------------------------
# Audio Sync
# -----------------------------------
def audio_sync(src, enc):
    duration = 10
    src_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    enc_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name

    run_cmd(["ffmpeg","-y","-i",src,"-t",str(duration),
             "-ac","1","-ar","16000",src_wav])

    run_cmd(["ffmpeg","-y","-i",enc,"-t",str(duration),
             "-ac","1","-ar","16000",enc_wav])

    y1, sr = sf.read(src_wav)
    y2, sr = sf.read(enc_wav)

    y1 = (y1 - np.mean(y1)) / (np.std(y1) + 1e-8)
    y2 = (y2 - np.mean(y2)) / (np.std(y2) + 1e-8)

    corr = np.correlate(y1, y2, "full")
    lag = corr.argmax() - (len(y1) - 1)

    return {
        "lag_samples": int(lag),
        "lag_ms": float((lag / sr) * 1000)
    }

# -----------------------------------
# Main
# -----------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--encoded", required=True)
    parser.add_argument("--output", default="fastpix_benchmark.json")
    args = parser.parse_args()

    print("Extracting frames...")
    src_frames = extract_frames(args.source, TMP_SRC, "src")
    enc_frames = extract_frames(args.encoded, TMP_ENC, "enc")

   print("Running comprehensive video quality benchmark...")

    results = {
        "video_quality": {
            **compute_vmaf_full(args.source, args.encoded),
            **compute_psnr_full(args.source, args.encoded)
        },
        "frame_analysis": frame_level_metrics(src_frames, enc_frames),
        "audio_sync": audio_sync(args.source, args.encoded)
    }

    with open(args.output, "w") as f:
        json.dump(results, f, indent=4)

    print("\n🏆 Video Quality Benchmark Complete")
    print(json.dumps(results, indent=4))

if __name__ == "__main__":
    main()
