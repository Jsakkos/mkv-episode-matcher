# MKV Episode Matcher

[![Documentation Status](https://img.shields.io/github/actions/workflow/status/Jsakkos/mkv-episode-matcher/documentation.yml?label=docs)](https://jsakkos.github.io/mkv-episode-matcher/)
[![PyPI version](https://img.shields.io/pypi/v/mkv-episode-matcher.svg)](https://pypi.org/project/mkv-episode-matcher/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automatically match and rename your MKV TV episodes using The Movie Database (TMDb).

## Features

- 🎯 **Automatic Episode Matching**: Uses TMDb to accurately identify episodes
- 📝 **Subtitle Extraction**: Extracts subtitles from MKV files
- 🔍 **OCR Support**: Handles image-based subtitles
- 🚀 **Multi-threaded**: Fast processing of multiple files
- ⬇️ **Subtitle Downloads**: Integration with OpenSubtitles
- ✨ **Bulk Processing**: Handle entire seasons at once
- 🧪 **Dry Run Mode**: Test changes before applying

## Quick Start

1. Install the package:
```bash
pip install mkv-episode-matcher
```

2. Run on your show directory:
```bash
mkv-match --show-dir "path/to/your/show" --season 1
```

## Requirements

- Python 3.8 or higher
- TMDb API key
- OpenSubtitles account (optional, for subtitle downloads)

## Documentation

Full documentation is available at [https://jsakkos.github.io/mkv-episode-matcher/](https://jsakkos.github.io/mkv-episode-matcher/)

## Basic Usage

```python
from mkv_episode_matcher import process_show

# Process all seasons
process_show()

# Process specific season
process_show(season=1)

# Test run without making changes
process_show(season=1, dry_run=True)

# Process and download subtitles
process_show(get_subs=True)
```

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

