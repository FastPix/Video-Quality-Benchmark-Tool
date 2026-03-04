# Video Quality Benchmark Tool

A frame-level video quality benchmarking tool built using Python + FFmpeg (libvmaf).

This tool performs deep objective quality analysis between a **source** video and an **encoded** video.

---

# Features

## Video Quality Metrics
- VMAF (Average, Min, Std Dev, Worst Frame)
- PSNR (Average, Std Dev, Worst Frame)
- Global SSIM
- Frame-level SSIM analysis

## Advanced Frame Analysis
- SSIM variance tracking
- Edge retention ratio & variance
- Noise difference & variance
- Temporal flicker score & variance
- Motion stability score & variance

## Audio Analysis
- Audio sync lag (samples)
- Audio sync lag (milliseconds)

---

# Requirements

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

To ensure FFmpeg is compiled with libvmaf (required for VMAF metrics):

```bash
brew install ffmpeg --with-libvmaf
```

Or, for other platforms, follow the official FFmpeg documentation to enable libvmaf during compilation.

---

# Installation

```bash
git clone https://github.com/FastPix/Video-Quality-Benchmark-Tool.git
cd Video-Quality-Benchmark-Tool

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

# Input File Structure

This repository includes two folders with demo video files:

```
source/
encoded/
```

- `source/` contains a sample reference video.
- `encoded/` contains a sample encoded/transcoded video.

**Note:** These are demo files for testing. For real benchmarking, upload your own videos to these folders and rename them as described below.

## Using Your Own Videos

To run the benchmark on your own videos:


1. Replace the demo file inside `source/` with your reference video.
2. Replace the demo file inside `encoded/` with your encoded/transcoded video.
3. **Rename your files to match the existing filenames.**

Example structure:

```
source/source.mp4
encoded/encoded.mp4
```


**Important:**
- Keep the same filenames (`source.mp4` and `encoded.mp4`)
- Both videos should ideally have the same resolution
- Both videos should have the same frame rate
- Both videos should have similar duration

---

# Notes

- **Processing Time:** Large video files will take significantly longer to process and analyze. Processing time depends on video length, resolution, and system performance.
- **File Names:** Always rename your uploaded videos to `source.mp4` and `encoded.mp4` for the tool to work correctly.
- **Demo Videos:** The `source/` and `encoded/` folders contain demo videos. Replace them with your own for real benchmarking.


---

# Run Benchmark

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

