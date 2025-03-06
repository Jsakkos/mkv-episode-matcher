# Quick Start Guide

Get started with MKV Episode Matcher quickly and efficiently.

## Basic Usage

### 1. Interactive Mode

Simply run:
```bash
mkv-match
```
The program will guide you through the setup interactively.

### 2. Command Line Options

Process a specific season:
```bash
mkv-match --show-dir "/path/to/show" --season 1
```

Process all seasons with subtitles:
```bash
mkv-match --show-dir "/path/to/show" --get-subs
```

Test run with detailed output:
```bash
mkv-match --show-dir "/path/to/show" --dry-run --verbose
```

## Key Features

- Interactive setup
- Progress bars with ETA
- Detailed matching information
- Confidence-based matching
- Automatic subtitle downloads
- GPU acceleration support

## Directory Structure

Expected TV show organization:
```
Show Name/
├── Season 1/
│   ├── episode1.mkv
│   ├── episode2.mkv
├── Season 2/
│   ├── episode1.mkv
│   └── episode2.mkv
```

## Configuration

Configuration is stored at `~/.mkv-episode-matcher/config.ini`:
```ini
[Config]
tmdb_api_key = your_tmdb_api_key
show_dir = /path/to/show
open_subtitles_api_key = your_opensubs_key
open_subtitles_user_agent = your_user_agent
open_subtitles_username = your_username
open_subtitles_password = your_password
```

## Common Commands

### Check GPU Support
```bash
mkv-match --check-gpu true
```

### Set Confidence Level
```bash
mkv-match --show-dir "/path/to/show" --confidence 0.8
```

### Enable Verbose Output
```bash
mkv-match --show-dir "/path/to/show" --verbose true
```

## Next Steps

- Read [Installation Guide](installation.md) for setup details
- Check [Tips and Tricks](tips.md) for advanced usage
- See [API Reference](api/index.md) for development
