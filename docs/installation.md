# Installation Guide

MKV Episode Matcher v1.0.0 offers multiple installation options including standalone executables, package managers, and development setups.

## 🚀 Quick Installation Options

### 1. Standalone Executables (Easiest)

Download ready-to-run applications with everything included:

**Windows:**
```powershell
# Download and extract
Invoke-WebRequest -Uri "https://github.com/Jsakkos/mkv-episode-matcher/releases/latest/download/MKVEpisodeMatcher-windows.zip" -OutFile "mkv-matcher.zip"
Expand-Archive "mkv-matcher.zip"
cd mkv-matcher
./MKVEpisodeMatcher.exe
```

**macOS:**
```bash
# Download and extract
curl -L "https://github.com/Jsakkos/mkv-episode-matcher/releases/latest/download/MKVEpisodeMatcher-macos.zip" -o mkv-matcher.zip
unzip mkv-matcher.zip
open MKVEpisodeMatcher.app
```

**Linux:**
```bash
# Download AppImage
wget "https://github.com/Jsakkos/mkv-episode-matcher/releases/latest/download/mkv-episode-matcher-linux.AppImage"
chmod +x mkv-episode-matcher-linux.AppImage
./mkv-episode-matcher-linux.AppImage
```

### 2. Package Installation

**Using uv (Recommended):**
```bash
# Basic installation
uv sync

# With CUDA GPU support (Windows/Linux only)
uv sync --extra cu128

# With development tools
uv sync --group dev
```

**Using pip:**
```bash
# Basic installation
pip install mkv-episode-matcher

# For GPU acceleration (after basic install)
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

## Prerequisites

### Required System Dependencies

**FFmpeg** (Required for audio extraction):

- **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) or use package manager:
  ```powershell
  winget install FFmpeg.FFmpeg
  # or
  choco install ffmpeg
  ```

- **macOS**: 
  ```bash
  brew install ffmpeg
  ```

- **Linux**: 
  ```bash
  # Ubuntu/Debian
  sudo apt install ffmpeg
  
  # RHEL/CentOS/Fedora
  sudo dnf install ffmpeg
  
  # Arch Linux
  sudo pacman -S ffmpeg
  ```

**Verification:**
```bash
ffmpeg -version
```

### Python Requirements (Package Installation Only)
- Python 3.10-3.12
- pip or uv package manager

## Installation Methods

### Method 1: uv Package Manager (Recommended)

**Install uv:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Install MKV Episode Matcher:**
```bash
# Clone repository
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Basic installation
uv sync

# With CUDA support (GPU acceleration)
uv sync --extra cu128

# Launch application
uv run mkv-match gui
```

### Method 2: pip Installation

```bash
# Install from PyPI
pip install mkv-episode-matcher

# Launch GUI
mkv-match gui

# Or launch CLI
mkv-match config
```

### Method 3: Development Installation

```bash
# Clone repository
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Install uv if not already installed
pip install uv

# Install with development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Launch application
uv run mkv-match gui
```

## GPU Acceleration Setup

### NVIDIA CUDA Support

**Windows/Linux with CUDA GPU:**
```bash
# Install with CUDA support
uv sync --extra cu128

# Verify GPU detection
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Requirements:**
- NVIDIA GPU with CUDA Compute Capability 6.0+
- CUDA Toolkit 12.8 or compatible
- At least 4GB VRAM recommended

**Benefits:**
- 5-10x faster speech recognition
- Better handling of large audio files
- Parallel processing capabilities

### CPU-Only Installation

For systems without CUDA support, the CPU installation works with:
- Intel/AMD processors
- Apple Silicon (M1/M2/M3)
- ARM processors

Performance will be slower but fully functional.

## Configuration Setup

### First-Time Configuration

**GUI Method (Easiest):**
1. Launch: `mkv-match gui` or run executable
2. Click the settings (⚙️) gear icon
3. Enter your API keys and preferences
4. Save configuration

**CLI Method:**
```bash
# Interactive setup
mkv-match config

# Direct configuration
mkv-match config \
  --tmdb-api-key "your_tmdb_key" \
  --opensub-api-key "your_opensub_key"
```

### Required API Keys

**OpenSubtitles API Key (Required for subtitle downloads):**
1. Visit [OpenSubtitles Developers](https://www.opensubtitles.com/consumers)
2. Create account and register application
3. Copy API key to configuration

**TMDb API Key (Optional, for enhanced metadata):**
1. Visit [TMDb API Settings](https://www.themoviedb.org/settings/api)
2. Request API key
3. Add to configuration

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10, macOS 12, Ubuntu 20.04 | Windows 11, macOS 13+, Ubuntu 22.04+ |
| **Python** | 3.10 | 3.12 |
| **RAM** | 4GB | 8GB+ |
| **Storage** | 2GB | 5GB+ (for model cache) |
| **GPU** | Optional | NVIDIA GTX 1060+ with 4GB+ VRAM |

## Verification

**Test Installation:**
```bash
# Check version
mkv-match --version

# Test configuration
mkv-match config --show

# Test GPU (if applicable)
uv run python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA Device: {torch.cuda.get_device_name()}")
"
```

**Test Basic Functionality:**
```bash
# Launch GUI (should open desktop application)
mkv-match gui

# Test CLI help
mkv-match --help
```

## Troubleshooting

### Common Installation Issues

**FFmpeg Not Found:**
```bash
# Test FFmpeg installation
ffmpeg -version

# If missing, install per platform instructions above
```

**Python Version Issues:**
```bash
# Check Python version
python --version

# Install compatible version if needed
```

**CUDA Installation Problems:**
```bash
# Check CUDA toolkit
nvcc --version

# Reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision torchaudio
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

**Permission Errors:**
```bash
# On Linux/macOS, try with user directory
pip install --user mkv-episode-matcher

# Or use virtual environment
python -m venv mkv-env
source mkv-env/bin/activate  # Linux/macOS
# mkv-env\Scripts\activate   # Windows
pip install mkv-episode-matcher
```

### Platform-Specific Issues

**macOS Issues:**
- **Apple Silicon**: Use native ARM64 Python, not x86_64
- **Rosetta**: May work but performance will be reduced
- **Security**: May need to allow unsigned applications

**Windows Issues:**
- **Antivirus**: Some AV software may flag executables
- **PATH**: Ensure FFmpeg is in system PATH
- **PowerShell**: Use PowerShell 5.1+ for best compatibility

**Linux Issues:**
- **Dependencies**: Install system packages for audio libraries
- **AppImage**: May need to install FUSE for older systems
- **Permissions**: Ensure execute permissions on binaries

### Getting Help

If you encounter issues:

1. **Check Logs**: Look in `~/.mkv-episode-matcher/logs/`
2. **Update Dependencies**: `pip install --upgrade mkv-episode-matcher`
3. **Community Support**: [GitHub Discussions](https://github.com/Jsakkos/mkv-episode-matcher/discussions)
4. **Bug Reports**: [GitHub Issues](https://github.com/Jsakkos/mkv-episode-matcher/issues)

Include the following in bug reports:
- Operating system and version
- Python version (`python --version`)
- Installation method used
- Full error message and traceback
- Log files from `~/.mkv-episode-matcher/logs/`