# MKV Episode Matcher

[![Development Status](https://img.shields.io/pypi/status/mkv-episode-matcher)](https://pypi.org/project/mkv-episode-matcher/)
[![PyPI version](https://img.shields.io/pypi/v/mkv-episode-matcher.svg)](https://pypi.org/project/mkv-episode-matcher/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://img.shields.io/github/actions/workflow/status/Jsakkos/mkv-episode-matcher/documentation.yml?label=docs)](https://jsakkos.github.io/mkv-episode-matcher/)
[![Downloads](https://static.pepy.tech/badge/mkv-episode-matcher)](https://pepy.tech/project/mkv-episode-matcher)

Automatically match and rename your MKV TV episodes using advanced speech recognition and subtitle matching.

## 🚀 Quick Start

Follow these steps to get up and running in minutes.

### 1. Prerequisites
Before you start, ensure you have the following:
*   **[FFmpeg](https://ffmpeg.org/download.html)**: Installed and added to your system PATH.
*   **API Keys**:
    *   **OpenSubtitles.com** account (for downloading subtitles).
    *   **TMDb** API Key (for fetching episode titles).

### 2. Install & Launch
**The easiest way to run MKV Episode Matcher is using the standalone Windows executable.**

1.  Download the latest `mkv-match.exe` from [GitHub Releases](https://github.com/Jsakkos/mkv-episode-matcher/releases).
2.  Double-click `mkv-match.exe` to launch.
3.  The Web UI will automatically open in your default browser at `http://localhost:8001`.

> [!NOTE]
> On the very first run, the system needs to download the speech recognition model (approx. 5-10 seconds). You will see a "System Loading" indicator.

### 3. Setup
1.  In the Web UI, go to the **Settings** tab.
2.  Enter your **OpenSubtitles** credentials and **TMDb API Key**.
3.  Click **Save**.

### 4. Make Your First Match
1.  Go to the **Dashboard**.
2.  Use the file browser to navigate to a folder containing your TV show episodes.
3.  Click **"Scan This Folder"**.
4.  The system will analyze your files and propose matches. You can review them before confirming the rename.

---

## ✨ Key Features
- **Modern Web Interface**: Easy-to-use Dashboard with dark mode.
- **Advanced Speech Recognition**: Identifies episodes by listening to the audio.
- **Smart Subtitles**: Automatically downloads subtitles from OpenSubtitles.
- **Safe**: Review matches before any files are renamed.

---

## 🛠️ Advanced Installation & Usage

For developers, Linux/macOS users, or those preferring the command line.

### Option A: Install via pip (Cross-platform)
```bash
# Basic install
pip install mkv-episode-matcher[cpu]

# With CUDA support (NVIDIA GPU required)
pip install mkv-episode-matcher[cu128]
```

### Option B: Run from Source (Development)
We recommend using [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Install dependencies
uv sync --extra cpu

# Launch Server
uv run mkv-match serve
```

### CLI Mode
You can also use the Command Line Interface (CLI) for automation.

```bash
# Match a folder
mkv-match match "C:\Path\To\Show"

# Match with subtitle download
mkv-match match "C:\Path\To\Show" --get-subs
```

### Building the Executable
To build the `.exe` yourself:
```bash
uv sync --extra cpu
uv run pyinstaller mkv_match.spec
```

---

## Reference Subtitle Structure
If you have your own subtitles or don't use the auto-download feature, ensure your files are named correctly so the system can find them.

**Cache Directory:** `C:\Users\{username}\.mkv-episode-matcher\cache\data\`

**Naming Format:**
`{show_name} - S{season:02d}E{episode:02d}.srt`

Example:
```
Show Name/
├── Show Name - S01E01.srt
├── Show Name - S01E02.srt
```

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Documentation
Full documentation is available at [https://jsakkos.github.io/mkv-episode-matcher/](https://jsakkos.github.io/mkv-episode-matcher/)
