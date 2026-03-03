# 🎥 Video Quality Benchmark Tool

A frame-level video quality benchmarking tool built using Python + FFmpeg (libvmaf).

This tool performs deep objective quality analysis between a **source** video and an **encoded** video.

---

# 🚀 Features

## 🎯 Video Quality Metrics
- VMAF (Average, Min, Std Dev, Worst Frame)
- PSNR (Average, Std Dev, Worst Frame)
- Global SSIM
- Frame-level SSIM analysis

## 🔬 Advanced Frame Analysis
- SSIM variance tracking
- Edge retention ratio & variance
- Noise difference & variance
- Temporal flicker score & variance
- Motion stability score & variance

## 🔊 Audio Analysis
- Audio sync lag (samples)
- Audio sync lag (milliseconds)

---

# 🛠 Requirements

- Python 3.9+
- FFmpeg compiled with libvmaf

Verify FFmpeg:

```bash
ffmpeg -filters | grep vmaf
```

If missing (macOS):

```bash
brew install ffmpeg
```

---

# 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/video-quality-benchmark.git
cd video-quality-benchmark

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

# 📁 Input File Structure

This repository includes two empty folders:

```
source/
encoded/
```

Place your videos as follows:

- Put the original reference video inside `source/`
- Put the encoded/transcoded video inside `encoded/`

Example:

```
source/source.mp4
encoded/encoded.mp4
```

Both videos should ideally have:
- Same resolution
- Same frame rate
- Same duration

---

# ▶️ Run Benchmark

```bash
python video_benchmark.py \
  --source source/source.mp4 \
  --encoded encoded/encoded.mp4 \
  --output result.json
```

---

# 📊 Example Output

```json
{
  "video_quality": {
    "vmaf_average": 97.30,
    "vmaf_min": 81.30,
    "vmaf_std": 2.54,
    "vmaf_worst_frame_index": 59,
    "psnr_average": 48.71,
    "psnr_std": 5.08,
    "psnr_worst_frame": 38.74,
    "psnr_worst_frame_index": 893
  },
  "frame_analysis": {
    "avg_frame_ssim": 0.9865,
    "min_frame_ssim": 0.9533,
    "ssim_std": 0.0071,
    "edge_retention_ratio": 0.955,
    "edge_variance": 75.48,
    "avg_noise_difference": -1.32,
    "noise_variance": 1.02,
    "temporal_flicker_score": 1.64,
    "flicker_variance": 6.54,
    "motion_stability_score": 0.845,
    "motion_variance": 0.125
  },
  "audio_sync": {
    "lag_samples": 0,
    "lag_ms": 0.0
  }
}
```

---

# 🔍 Use Cases

- Encoder comparison (AWS / GCP / custom pipeline)
- Transcoding validation
- Video compression benchmarking
- Quality regression testing
- Detecting flicker and motion instability

---

