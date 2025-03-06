# Command Line Interface

The CLI features a rich, user-friendly interface with color-coded output and progress indicators.

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

| Option           | Description                 | Default    |
| ---------------- | --------------------------- | ---------- |
| `--show-dir`     | Show directory path         | None       |
| `--season`       | Season number to process    | None (all) |
| `--dry-run`      | Test without making changes | False      |
| `--get-subs`     | Download subtitles          | False      |
| `--tmdb-api-key` | TMDb API key                | None       |

## Examples

### Dry Run Mode

```bash
mkv-match --show-dir "/path/to/show" --dry-run
```

### Download Subtitles

```bash
mkv-match --show-dir "/path/to/show" --get-subs
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
  --get-subs \
  --dry-run
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
