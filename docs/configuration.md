# Configuration Guide

## Configuration File

MKV Episode Matcher uses a configuration file located at:

- Windows: `%USERPROFILE%\.mkv-episode-matcher\config.ini`
- Linux/Mac: `~/.mkv-episode-matcher/config.ini`

## Configuration Options

```ini
[Config]
# Required Settings
tmdb_api_key = your_tmdb_api_key
show_dir = /path/to/shows

# Optional Settings
max_threads = 4
open_subtitles_api_key = your_opensubs_key
open_subtitles_user_agent = your_user_agent
open_subtitles_username = your_username
open_subtitles_password = your_password
tesseract_path = /path/to/tesseract
```

## Command Line Configuration

All configuration options can be set via command line:

```bash
mkv-match \
  --tmdb-api-key "your_key" \
  --show-dir "/path/to/shows" \
  --season 1 \
  --dry-run true \
  --get-subs true \
  --tesseract-path "/path/to/tesseract"
```

## Environment Variables

You can also use environment variables:

```bash
export TMDB_API_KEY="your_key"
export SHOW_DIR="/path/to/shows"
export OPEN_SUBTITLES_API_KEY="your_key"
```

## Configuration Priority

Settings are loaded in the following order (later overrides earlier):

1. Default values
2. Configuration file
3. Environment variables
4. Command line arguments

## Detailed Options

### TMDb Configuration

```ini
[Config]
tmdb_api_key = your_api_key
```

The TMDb API key is required for:
- Show identification
- Episode information
- Season details

### OpenSubtitles Configuration

```ini
[Config]
open_subtitles_api_key = your_key
open_subtitles_user_agent = your_agent
open_subtitles_username = username
open_subtitles_password = password
```

Required only if using subtitle download functionality.

### Performance Settings

```ini
[Config]
max_threads = 4
```

Adjust based on your system's capabilities:
- Default: 4 threads
- Minimum: 1 thread
- Maximum: Number of CPU cores

### OCR Configuration

```ini
[Config]
tesseract_path = /path/to/tesseract
```

Required only if processing image-based subtitles.
