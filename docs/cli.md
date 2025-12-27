# Command Line Interface

The MKV Episode Matcher CLI features a rich, user-friendly interface with color-coded output and progress indicators.

## Basic Usage

### Interactive Configuration

```bash
# First-time setup wizard
mkv-match config

# Show current configuration
mkv-match config --show

# Set specific values
mkv-match config --tmdb-api-key "your_key" --opensub-api-key "your_key"
```

### Processing Files and Directories

```bash
# Process a single MKV file
mkv-match match "/path/to/episode.mkv"

# Process an entire series folder
mkv-match match "/path/to/Show/Season 1/"

# Process entire library with subtitle downloads
mkv-match match "/path/to/library/" --get-subs
```

### GUI Mode

```bash
# Launch desktop application
mkv-match gui
```

## Core Commands

| Command    | Description                          |
| ---------- | ------------------------------------ |
| `config`   | Manage configuration settings        |
| `match`    | Process and match MKV files          |
| `gui`      | Launch desktop graphical interface   |

## Match Command Options

| Option              | Description                      | Default    |
| ------------------- | -------------------------------- | ---------- |
| `path`              | File or directory to process     | Required   |
| `--season`          | Season number to process         | Auto-detect |
| `--dry-run`         | Test without making changes      | False      |
| `--get-subs`        | Download subtitles               | False      |
| `--confidence`      | Minimum confidence threshold     | 0.8        |
| `--output-dir`      | Copy files to directory          | None       |
| `--json`            | JSON output for automation       | False      |
| `--verbose`         | Verbose logging output           | False      |

## Configuration Options

| Option                | Description                     | Example                    |
| --------------------- | ------------------------------- | -------------------------- |
| `--tmdb-api-key`      | TMDb API key                    | `--tmdb-api-key "key"`     |
| `--opensub-api-key`   | OpenSubtitles API key           | `--opensub-api-key "key"`  |
| `--opensub-username`  | OpenSubtitles username          | `--opensub-username "user"` |
| `--opensub-password`  | OpenSubtitles password          | `--opensub-password "pass"` |
| `--cache-dir`         | Cache directory path            | `--cache-dir "/custom"`    |
| `--confidence`        | Confidence threshold (0.0-1.0)  | `--confidence 0.85`        |
| `--show`              | Show current configuration      | `--show`                   |

## Examples

### First-Time Setup

```bash
# Interactive configuration
mkv-match config

# Or set values directly
mkv-match config \
  --tmdb-api-key "your_tmdb_key" \
  --opensub-api-key "your_opensub_key" \
  --opensub-username "your_username" \
  --opensub-password "your_password"
```

### Basic Processing

```bash
# Process with dry run
mkv-match match "/path/to/Show/Season 1/" --dry-run

# Process and download subtitles
mkv-match match "/path/to/Show/Season 1/" --get-subs

# Process specific season only
mkv-match match "/path/to/Show/" --season 1
```

### Advanced Processing

```bash
# Copy to output directory instead of renaming
mkv-match match "/path/to/show/" --output-dir "/path/to/renamed/"

# JSON output for automation
mkv-match match "/path/to/library/" --json --output-dir "/processed/"

# High confidence matching with verbose output
mkv-match match "/path/to/show/" --confidence 0.9 --verbose
```

### Batch Processing

```bash
# Process entire library efficiently (recommended)
mkv-match match "/path/to/library/" --get-subs

# Process multiple shows with consistent settings
for show in /path/to/library/*/; do
  mkv-match match "$show" --get-subs --confidence 0.85
done
```

## Logging

Logs are stored in:
```
~/.mkv-episode-matcher/logs/
├── stdout.log
└── stderr.log
```

## Tips

1. Always use quotes around paths
2. Use dry-run first to test
3. Check logs for details
4. Use full paths for reliability
5. Avoid using a trailing slash in paths
