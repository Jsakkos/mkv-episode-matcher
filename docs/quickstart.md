# Quick Start Guide

Get started with MKV Episode Matcher in minutes.

## Basic Usage

### 1. Process a Single Season

```bash
mkv-match --show-dir "/path/to/show" --season 1
```

### 2. Process All Seasons

```bash
mkv-match --show-dir "/path/to/show"
```

### 3. Test Run (No Changes)

```bash
mkv-match --show-dir "/path/to/show" --dry-run true
```

### 4. Download Subtitles

```bash
mkv-match --show-dir "/path/to/show" --get-subs true
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

## Reference Subtitle File Structure

Subtitle files that are not automatically downloaded using the `--get-subs` flag should be named as follows:

```plaintext
~/.mkv-episode-matcher/cache/data/Show Name/
├── Show Name - S01E01.srt
├── Show Name - S01E02.srt
└── ...
```

## Configuration

The configuration file is automatically generated at `~/.mkv-episode-matcher/config.ini`:

```ini
[Config]
tmdb_api_key = your_tmdb_api_key
show_dir = /path/to/show
max_threads = 4
open_subtitles_api_key = your_opensubs_key
open_subtitles_user_agent = your_user_agent
open_subtitles_username = your_username
open_subtitles_password = your_password
tesseract_path = C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Next Steps

- Check the [Configuration Guide](configuration.md) for detailed setup
- See [Tips and Tricks](tips.md) for advanced usage
- Browse the [API Reference](api/episode_matcher.md) for detailed documentation
