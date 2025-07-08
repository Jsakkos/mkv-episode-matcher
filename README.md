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

Automatically match and rename your MKV TV episodes using The Movie Database (TMDb).

## Features

- 🎯 **Automatic Episode Matching**: Uses TMDb and OpenSubtitles to accurately identify episodes
- 🔊 **Speech Recognition**: Uses OpenAI Whisper for accurate episode identification
- ⬇️ **Subtitle Downloads**: Integration with OpenSubtitles
- ✨ **Bulk Processing**: Handle entire seasons at once
- 🧪 **Dry Run Mode**: Test changes before applying

## Prerequisites

- Python 3.9-3.12
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in system PATH
- TMDb API key (optional, for subtitle downloads)
- OpenSubtitles account (optional, for subtitle downloads)

## Quick Start

1. Install the package:
```bash
pip install -U mkv-episode-matcher
```
2. Run onboarding to set up your configuration (first-time users or to update credentials):
```bash
mkv-match --onboard
```
   - You will be prompted for:
     - TMDb API key (for episode matching)
     - OpenSubtitles API key, Consumer Name, Username, and Password (for subtitle downloads)
     - Show Directory (main directory of your show)
   - If a config value already exists, you can accept the default or enter a new value.

3. 
   a. If you setup the TMDb and Opensubtitles credentials above, automatically fetch subtitles with the `--get-subs` flag. 
   b. Alternatively, manually download .srt subtitles files to ~/.mkv-episode-matcher/cache/data/Show Name/

4. Run on your show directory:
```bash
mkv-match --show-dir "path/to/your/show"
```

## Onboarding & Configuration

The onboarding process will prompt you for all required configuration values if you run with `--onboard` or if no config file exists. You can re-run onboarding at any time to update your credentials or show directory.

**Required information:**
- TMDb API key (for episode matching)
- OpenSubtitles API key (for subtitle downloads)
- OpenSubtitles Consumer Name (for subtitle downloads)
- OpenSubtitles Username (for subtitle downloads)
- OpenSubtitles Password (for subtitle downloads)
- Show Directory (main directory of your show)

If a value already exists, it will be shown as the default and you can accept it or enter a new value.

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
