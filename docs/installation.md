# Installation Guide

## Basic Installation

Install MKV Episode Matcher using pip:

```bash
pip install mkv-episode-matcher
```

## Installation Options

### GPU Support

For GPU acceleration (recommended if you have a CUDA-capable GPU):

```bash
pip install "mkv-episode-matcher"
```
Find the appropriate CUDA version and upgrade Torch (e.g., for CUDA 12.4):
```bash
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```


### Development Installation

For contributing or development:

```bash
# Clone the repository
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Install UV
pip install uv

# Install with development dependencies
uv venv
uv pip install -e ".[dev]"
```

## API Keys Setup

1. **TMDb API Key**
    - Create an account at [TMDb](https://www.themoviedb.org/)
    - Go to your account settings
    - Request an API key

2. **OpenSubtitles (Optional)**
    - Register at [OpenSubtitles](https://www.opensubtitles.com/)
    - Get your API key from the dashboard

## System Requirements

### For GPU Support
- CUDA-capable NVIDIA GPU
- CUDA Toolkit 12.1 or compatible version
- At least 4GB GPU memory recommended for Whisper speech recognition

### For CPU-Only
- No special requirements beyond Python 3.9+

## Verification

Verify your installation:

```bash
mkv-match --version

# Check GPU availability (if installed with GPU support)
python -c "import torch; print(f'GPU available: {torch.cuda.is_available()}')"
```

## Troubleshooting

If you encounter any issues:
1. Ensure you have the latest pip: `pip install --upgrade pip`
2. For GPU installations, verify CUDA is properly installed
3. Check the [compatibility matrix](https://pytorch.org/get-started/locally/) for PyTorch and CUDA versions
4. If you encounter any other issues, please [open an issue](https://github.com/Jsakkos/mkv-episode-matcher/issues) on GitHub