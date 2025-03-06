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

### Performance & Accuracy

1. **Confidence Threshold**
   ```bash
   # Increase matching accuracy (default: 0.7)
   mkv-match --show-dir "/path/to/show" --confidence 0.8
   ```
   Start with a higher value and decrease if needed. Lower values may result in false positives.

2. **Batch Processing with Progress**
   The tool now shows detailed progress for each season:
   ```bash
   mkv-match --show-dir "/path/to/show"
   ```

3. **Speech Recognition**
   - Uses Whisper for audio analysis
   - Processes files in parallel for speed
   - Shows real-time progress with completion estimates


## Advanced Usage

### Testing Changes

Always use dry-run first:
```bash
mkv-match --show-dir "/path/to/show" --dry-run true
```

### Debug Output

Enable verbose logging:
```bash
mkv-match --show-dir "/path/to/show" -v
```

### Log Files

Check the logs at:
```
~/.mkv-episode-matcher/logs/
├── stdout.log  # General operation logs
└── stderr.log  # Error and warning logs
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

3. **Speech Recognition**
   - GPU recommended for faster processing
   - Processing happens in 30s intervals
   - More accurate than OCR-based methods


4. **Low Confidence Matches**
   - Increase confidence threshold
   - Check reference subtitles for accuracy

5. **No Matches Found**
   - Verify file organization
   - Check reference subtitles
   - Enable verbose output

6. **Performance Issues**
   - Process one season at a time
   - Check available disk space
   - Monitor system resources