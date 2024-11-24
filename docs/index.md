# MKV Episode Matcher

Welcome to the MKV Episode Matcher documentation! This tool helps you automatically organize and rename your TV show episodes using information from The Movie Database (TMDb).

## Features

- 🎯 **Automatic Episode Matching**: Uses TMDb to accurately identify episodes
- 📝 **Subtitle Extraction**: Extracts subtitles from MKV files
- 🔍 **OCR Support**: Handles image-based subtitles
- 🚀 **Multi-threaded**: Fast processing of multiple files
- ⬇️ **Subtitle Downloads**: Integration with OpenSubtitles
- ✨ **Bulk Processing**: Handle entire seasons at once
- 🧪 **Dry Run Mode**: Test changes before applying

## Quick Example

```bash
# Install the package
pip install mkv-episode-matcher

# Run on a show directory
mkv-match --show-dir "path/to/your/show" --season 1
```

## Project Overview

MKV Episode Matcher solves the common problem of organizing TV show libraries by:

1. Analyzing MKV files in your show directory
2. Extracting and processing subtitles
3. Matching episodes with TMDb database
4. Renaming files to a consistent format

## Requirements

- Python 3.8 or higher
- TMDb API key
- OpenSubtitles account (optional, for subtitle downloads)

## Getting Help

- Check the [Quick Start Guide](quickstart.md) for basic usage
- See [Configuration](configuration.md) for setup details
- Browse the [API Reference](api/episode_matcher.md) for detailed documentation
- Visit our [GitHub repository](https://github.com/Jsakkos/mkv-episode-matcher) for issues and updates
