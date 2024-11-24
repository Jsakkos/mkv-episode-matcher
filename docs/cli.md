# Command Line Interface

## Basic Commands

### Process Show

```bash
mkv-match --show-dir "/path/to/show"
```

### Process Specific Season

```bash
mkv-match --show-dir "/path/to/show" --season 1
```

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--show-dir` | Show directory path | None |
| `--season` | Season number to process | None (all) |
| `--dry-run` | Test without making changes | False |
| `--get-subs` | Download subtitles | False |
| `--tmdb-api-key` | TMDb API key | None |
| `--tesseract-path` | Path to Tesseract | None |

## Examples

### Dry Run Mode

```bash
mkv-match --show-dir "/path/to/show" --dry-run true
```

### Download Subtitles

```bash
mkv-match --show-dir "/path/to/show" --get-subs true
```

### Set API Key

```bash
mkv-match --show-dir "/path/to/show" --tmdb-api-key "your_key"
```

### Multiple Options

```bash
mkv-match \
  --show-dir "/path/to/show" \
  --season 1 \
  --get-subs true \
  --dry-run true
```

## Environment Variables

Alternative to command line options:

```bash
export TMDB_API_KEY="your_key"
export SHOW_DIR="/path/to/shows"
mkv-match
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | API error |

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
