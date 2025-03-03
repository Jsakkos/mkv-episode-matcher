# Tips and Tricks

## Best Practices

### Directory Organization

Organize your files consistently:
```
TV Shows/
├── Show Name/
│   ├── Season 1/
│   │   ├── episode1.mkv
│   │   └── episode2.mkv
│   └── Season 2/
│       ├── episode1.mkv
│       └── episode2.mkv
```

### Performance Optimization

1. **Thread Configuration**
   ```ini
   [Config]
   max_threads = 4  # Adjust based on CPU cores
   ```

2. **Batch Processing**
   ```bash
   # Process multiple seasons
   for i in {1..5}; do
     mkv-match --show-dir "/path/to/show" --season $i
   done
   ```

### Error Handling

1. Always use dry-run first:
   ```bash
   mkv-match --show-dir "/path/to/show" --dry-run true
   ```

2. Check logs regularly:
   ```bash
   tail -f ~/.mkv-episode-matcher/logs/stderr.log
   ```

## Advanced Usage

### Custom Matching

```python
from mkv_episode_matcher import process_show

# Custom matching with specific settings
process_show(
    season=1,
    dry_run=True,
    get_subs=True
)
```

### Subtitle Processing

1. Extract subtitles only:
   ```python
   from mkv_episode_matcher.mkv_to_srt import convert_mkv_to_srt
   convert_mkv_to_srt(season_path, mkv_files)
   ```

2. Download specific subtitles:
   ```python
   from mkv_episode_matcher.utils import get_subtitles
   get_subtitles(show_id, {1, 2, 3})  # Seasons 1, 2, 3
   ```

## Troubleshooting

### Common Issues

1. **File Permission Errors**
   ```bash
   # Check file permissions
   chmod -R 644 "/path/to/show"
   ```

2. **API Rate Limits**
   - Use rate limiting in configuration
   - Implement exponential backoff

3. **Memory Usage**
   - Reduce max_threads
   - Process seasons separately

## Maintenance

### Clean Up

1. Remove temporary files:
   ```python
   from mkv_episode_matcher.utils import cleanup_ocr_files
   cleanup_ocr_files(show_dir)
   ```

2. Clear cache:
   ```bash
   rm -rf ~/.mkv-episode-matcher/cache/*
   ```

### Backup Strategy

1. Create backups before processing:
   ```bash
   cp -r "/path/to/show" "/path/to/backup"
   ```

2. Use dry-run to verify changes:
   ```bash
   mkv-match --show-dir "/path/to/show" --dry-run true
   ```

## Integration Tips

### Automation

1. **Cron Jobs**
   ```bash
   # Check for new episodes daily
   0 0 * * * mkv-match --show-dir "/path/to/show" --get-subs true
   ```

2. **Watch Folders**
   ```python
   # Monitor for new files
   from watchdog.observers import Observer
   from watchdog.events import FileSystemEventHandler
   ```

### API Usage

1. Rate limiting:
   ```python
   from mkv_episode_matcher.tmdb_client import RateLimitedRequest
   request = RateLimitedRequest(rate_limit=30, period=1)
   ```

2. Cache management:
   ```python
   # Cache API responses
   import shelve
   with shelve.open('cache') as db:
       # Cache operations
   ```
