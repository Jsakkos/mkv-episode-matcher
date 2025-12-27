# MKV Episode Matcher

[![Development Status](https://img.shields.io/pypi/status/mkv-episode-matcher)](https://pypi.org/project/mkv-episode-matcher/)
[![PyPI version](https://img.shields.io/pypi/v/mkv-episode-matcher.svg)](https://pypi.org/project/mkv-episode-matcher/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://img.shields.io/github/actions/workflow/status/Jsakkos/mkv-episode-matcher/documentation.yml?label=docs)](https://jsakkos.github.io/mkv-episode-matcher/)
[![Downloads](https://static.pepy.tech/badge/mkv-episode-matcher)](https://pepy.tech/project/mkv-episode-matcher)
[![GitHub last commit](https://img.shields.io/github/last-commit/Jsakkos/mkv-episode-matcher)](https://github.com/Jsakkos/mkv-episode-matcher/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/Jsakkos/mkv-episode-matcher)](https://github.com/Jsakkos/mkv-episode-matcher/issues)
[![Tests](https://github.com/Jsakkos/mkv-episode-matcher/actions/workflows/tests.yml/badge.svg)](https://github.com/Jsakkos/mkv-episode-matcher/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/Jsakkos/mkv-episode-matcher/branch/main/graph/badge.svg)](https://codecov.io/gh/Jsakkos/mkv-episode-matcher/)

Automatically match and rename your MKV TV episodes using advanced speech recognition and subtitle matching.

## ✨ Key Features

- 🖥️ **Modern Desktop GUI**: Cross-platform Flet-based graphical interface with real-time progress tracking
- 🤖 **Advanced Speech Recognition**: NVIDIA Parakeet ASR for highly accurate episode identification
- 🎯 **Intelligent Matching**: Multi-segment analysis with confidence scoring and fallback strategies
- ⬇️ **Smart Subtitle Integration**: Automatic subtitle downloads from OpenSubtitles with local caching
- ✨ **Bulk Processing**: Handle entire libraries with automatic series/season detection
- 🧪 **Dry Run Mode**: Preview matches before making any changes
- 📊 **Rich Progress Tracking**: Real-time progress indicators and detailed match results
- ⚡ **Performance Optimized**: Caching, background model loading, and efficient processing
- 🌐 **Cross-Platform**: Available as desktop applications for Windows, macOS, and Linux

## Prerequisites

- Python 3.10-3.12
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in system PATH
- TMDb API key (optional, for episode matching)
- OpenSubtitles.com account (required for subtitle downloads)

## 🚀 Quick Start

### 1. Install MKV Episode Matcher

**Option A: Using uv (Recommended)**
```bash
# Install with CUDA support for GPU acceleration
uv sync --extra cu128

# Or basic installation
uv sync
```

**Option B: Using pip**
```bash
pip install mkv-episode-matcher
```

**Option C: Download Standalone Desktop Apps**
- [Windows Executable](https://github.com/Jsakkos/mkv-episode-matcher/releases/latest/download/MKVEpisodeMatcher-windows.zip)
- [macOS Application](https://github.com/Jsakkos/mkv-episode-matcher/releases/latest/download/MKVEpisodeMatcher-macos.zip)
- [Linux AppImage](https://github.com/Jsakkos/mkv-episode-matcher/releases/latest/download/mkv-episode-matcher-linux.AppImage)

### 2. Launch the Application

**🖥️ GUI Mode (Recommended)**
Launches the modern desktop interface with real-time progress tracking:
```bash
uv run mkv-match gui
```

**💻 CLI Mode**  
For automation and advanced users:
```bash
uv run mkv-match match "/path/to/your/show"
```

**⚙️ Configuration**
```bash
uv run mkv-match config
```

### 3. Alternative Launch Methods
```bash
# GUI
python -m mkv_episode_matcher gui

# CLI
python -m mkv_episode_matcher match "/path/to/show"
```
## 🖥️ Desktop GUI Features

The modern Flet-based desktop interface provides:

- **🎨 Theme-Adaptive Interface**: Automatically adapts to your system's light/dark theme
- **📂 Folder Browser**: Easy directory selection with visual folder picker
- **⏱️ Real-time Progress**: Live progress bars showing "Processing file X of Y"
- **🔄 Background Model Loading**: Non-blocking ASR model initialization with status indicators  
- **🧪 Dry Run Preview**: Test matches without making changes, with preview functionality
- **⚙️ Comprehensive Settings**: Built-in configuration dialog for all options
- **📊 Detailed Results**: Color-coded success/failure results with confidence scores
- **🚀 Performance Indicators**: Model loading status and processing statistics

## ⚙️ Configuration

### GUI Configuration
The desktop app includes a built-in settings dialog accessible via the gear icon. Configure all options including:
- Cache directory and confidence thresholds
- ASR and subtitle provider settings  
- OpenSubtitles API credentials
- TMDb integration (optional)

### CLI Configuration
For command-line users:
```bash
mkv-match config  # Interactive configuration
mkv-match --onboard  # First-time setup wizard
```

**Required API Keys:**
- **OpenSubtitles API Key**: Required for subtitle downloads ([Get one here](https://www.opensubtitles.com/consumers))
- **TMDb API Key**: Optional, for enhanced episode metadata ([Get one here](https://www.themoviedb.org/settings/api))

**OpenSubtitles Setup:**
- Username and password (recommended for better rate limits)
- API key from the OpenSubtitles developer console

## Directory Structure

MKV Episode Matcher expects your TV shows to be organized as follows:

```
Show Name/
├── Season 1/
│   ├── episode1.mkv
│   ├── episode2.mkv
├── Season 2/
│   ├── episode1.mkv
│   └── episode2.mkv
```

## Reference Subtitle File Structure

Subtitle files that are not automatically downloaded using the `--get-subs` flag should be named as follows:

```

~/.mkv-episode-matcher/cache/data/Show Name/
├── Show Name - S01E01.srt
├── Show Name - S01E02.srt
└── ...
```

On Windows, the cache directory is located at `C:\Users\{username}\.mkv-episode-matcher\cache\data\`

Reference subtitle files should follow this naming pattern:
`{show_name} - S{season:02d}E{episode:02d}.srt`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- [TMDb](https://www.themoviedb.org/) for their excellent API
- [OpenSubtitles](https://www.opensubtitles.com/) for subtitle integration
- All contributors who have helped improve this project

## Documentation

Full documentation is available at [https://jsakkos.github.io/mkv-episode-matcher/](https://jsakkos.github.io/mkv-episode-matcher/)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes.
