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

## Python API Usage

```python
from mkv_episode_matcher import process_show

# Process all seasons
process_show()

# Process specific season
process_show(season=1)

# Test run
process_show(season=1, dry_run=True)

# With subtitles
process_show(season=1, get_subs=True)
```

## Configuration

Create a configuration file at `~/.mkv-episode-matcher/config.ini`:

```ini
[Config]
tmdb_api_key = your_api_key
open_subtitles_api_key = your_opensubs_key
show_dir = /path/to/shows
max_threads = 4
```

## Next Steps

- Check the [Configuration Guide](configuration.md) for detailed setup
- See [Tips and Tricks](tips.md) for advanced usage
- Browse the [API Reference](api/episode_matcher.md) for detailed documentation
