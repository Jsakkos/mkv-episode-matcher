# Installation Guide

MKV Episode Matcher v1.0.0 offers multiple installation options. The recommended method for Windows users is the Standalone Executable.

## 🚀 Quick Installation Options

### Windows Executable (Recommended)
1. Download `mkv-match.exe` from **[GitHub Releases](https://github.com/Jsakkos/mkv-episode-matcher/releases)**.
2. Run it. No Python installation required.

### Package Installation (Cross-Platform)

**Using uv (Recommended for Devs):**
```bash
uv sync --extra cpu    # Basic
uv sync --extra cu128  # CUDA GPU
```

**Using pip:**
```bash
pip install mkv-episode-matcher
```

## Prerequisites

### 1. FFmpeg (Required)
You must have FFmpeg installed and in your system PATH for audio extraction.

- **Windows**: `winget install FFmpeg.FFmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

**Verification:**
```bash
ffmpeg -version
```

### 2. Python (Only if not using Executable)
- Python 3.10 - 3.12
- pip or uv package manager

## Installation Methods

### Method 1: Windows Standalone Executable
This is a self-contained binary that includes everything you need (except FFmpeg).

1.  **Download**: Get the latest `.exe` from [Releases](https://github.com/Jsakkos/mkv-episode-matcher/releases).
2.  **Run**: Double-click `mkv-match.exe`.
3.  **Use**: The Web UI will launch automatically.

### Method 2: uv Package Manager (Recommended for Python users)

**Install uv:**
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install & Run:**
```bash
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Install
uv sync --extra cpu   # or cu128 for GPU

# Run
uv run mkv-match gui
```

### Method 3: pip Installation

```bash
# Install
pip install mkv-episode-matcher

# Run
mkv-match gui
```

### Method 4: Development Installation

```bash
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher
pip install uv
uv sync --group dev
uv run pytest
```

## GPU Acceleration Setup (Optional)

If you have an NVIDIA GPU, you can speed up speech recognition significantly.

**Requirement:**
- NVIDIA GPU with CUDA support.
- Standalone Executable: Use the GPU-enabled build (if available) or Python install.
- Python Install:
  ```bash
  uv sync --extra cu128
  # or
  pip install mkv-episode-matcher[cu128]
  ```

## Configuration

**GUI (Easiest):**
Launch the app and use the Settings ⚙️ icon.

**CLI:**
```bash
mkv-match config
```

### API Keys
- **OpenSubtitles**: For subtitles. [Get Key](https://www.opensubtitles.com/consumers).
- **TMDb**: For metadata. [Get Key](https://www.themoviedb.org/settings/api).

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 12, Linux | Windows 11, macOS 13+ |
| **RAM** | 4GB | 8GB+ |
| **GPU** | None (CPU) | NVIDIA GTX 1060+ (4GB VRAM) |

## Troubleshooting

**FFmpeg Not Found:**
Run `ffmpeg -version` in a terminal. If it fails, reinstall FFmpeg or add it to your PATH.

**Permission Errors:**
Try installing with `--user`:
`pip install --user mkv-episode-matcher`

**Logs:**
Check `~/.mkv-episode-matcher/logs/` if the application fails to start.