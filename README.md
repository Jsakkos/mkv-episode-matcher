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

- 🌐 **Modern Web Interface**: Premium React-based UI with glassmorphism design and dark mode
- 🤖 **Advanced Speech Recognition**: OpenAI Whisper ASR via faster-whisper for accurate episode identification
- 🎯 **Intelligent Matching**: Multi-segment analysis with confidence scoring and fallback strategies
- ⬇️ **Smart Subtitle Integration**: Automatic subtitle downloads from OpenSubtitles with local caching
- ✨ **Bulk Processing**: Handle entire libraries with automatic series/season detection
- 📊 **Real-time Progress**: WebSocket-powered progress tracking with live updates
- ⚡ **Performance Optimized**: Caching, background model loading, and efficient processing
- 🐳 **Docker Ready**: Easy deployment via Docker or local execution

> [!NOTE]
> **First-Time Model Loading**: The Whisper ASR model takes approximately **5-10 seconds** to download and load on first use. The web UI shows a "System Loading" indicator during this time. Subsequent operations reuse the cached model and are much faster.

## Prerequisites

- Python 3.10-3.12
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in system PATH
- TMDb API key (optional, for episode matching)
- OpenSubtitles.com account (required for subtitle downloads)

## 🚀 Quick Start

### 1. Install MKV Episode Matcher

**Option A: pip (Easiest for end users)**
```bash
pip install mkv-episode-matcher
```

**Option B: From Source with uv (For development/latest features)**

First, install [uv](https://docs.astral.sh/uv/) if you don't have it:
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone and install:
```bash
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Basic installation
uv sync

# Or with CUDA support for GPU acceleration
uv sync --extra cu128
```

> For complete installation options, see the [Installation Guide](https://jsakkos.github.io/mkv-episode-matcher/installation/).

### 2. Launch the Application

**🌐 Web interface (Recommended)**
Launches the modern web interface in your default browser:
```bash
uv run python -m mkv_episode_matcher
```
Access the UI at `http://localhost:8001`

**💻 CLI Mode**
For automation and advanced users:
```bash
python -m mkv_episode_matcher match "/path/to/your/show"
```

**⚙️ Configuration**
Configuration is now managed directly through the web interface or via config files.

### 3. Build Standalone Executable
You can build a self-contained executable that bundles the backend and frontend:

```bash
uv run pyinstaller mkv_match.spec
# Output in dist/mkv-match/
```

## 🖥️ Web Interface Features

The new React-based interface provides:

- **🎨 Premium Design**: Modern aesthetics with glassmorphism and smooth animations
- **📂 Visual File Browser**: Intuitive navigation of your local file system
- **⏱️ Live Status**: Real-time job tracking via WebSockets
- **📱 Responsive**: Works identically on local machine or remote server access

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
