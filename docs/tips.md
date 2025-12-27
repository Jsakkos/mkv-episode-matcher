# Tips and Tricks

Essential tips for getting the most out of MKV Episode Matcher v1.0.0.

## 🎯 Best Practices

### Directory Organization

Organize your files consistently for optimal results:
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

**Supported patterns:**
- `Show Name/Season X/` - Standard Plex structure
- `Show Name/S01/` - Short season format
- `Show Name/Series 1/` - BBC/UK format

### ⚡ Performance Optimization

#### 🔥 Batch Processing (CRITICAL)

**DO THIS:** Process entire folders at once
```bash
# ✅ EFFICIENT: Model loads once for entire season
mkv-match match "/path/to/Show/Season 1/"

# ✅ EVEN BETTER: Process entire show
mkv-match match "/path/to/Show/"

# ✅ BEST: Process library with subtitles
mkv-match match "/path/to/library/" --get-subs
```

**DON'T DO THIS:** Process files individually
```bash
# ❌ INEFFICIENT: Parakeet model reloads for each file (30-60s each)
mkv-match match "/path/to/episode1.mkv"
mkv-match match "/path/to/episode2.mkv"
mkv-match match "/path/to/episode3.mkv"
```

**Why batch processing matters:**
- Parakeet ASR model takes 30-60 seconds to initialize
- Single initialization can process entire season
- 10x faster for multi-file operations
- Better memory management with bounded caching

#### GPU vs CPU Performance

**GPU Acceleration (Recommended):**
```bash
# Install with CUDA support
uv sync --extra cu128

# Verify GPU detection
uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

**Performance comparison:**
- **GPU**: 5-10x faster processing
- **CPU**: Fully functional but slower
- **Apple Silicon**: Good CPU performance on M1/M2/M3

#### Model Caching

The application automatically caches:
- **ASR models** (persistent across runs)
- **Audio chunks** (temporary during processing)  
- **Subtitle content** (session-based)
- **Video metadata** (LRU cache)

**Cache management:**
```bash
# Check cache statistics
mkv-match config --show

# Clear cache if needed
rm -rf ~/.mkv-episode-matcher/cache/
```

### 🎚️ Accuracy Tuning

#### Confidence Threshold

```bash
# Default: 0.8 (80% confidence)
mkv-match match "/path/to/show/" --confidence 0.8

# Conservative (fewer false positives)
mkv-match match "/path/to/show/" --confidence 0.9

# Aggressive (catch more matches, may have false positives)
mkv-match match "/path/to/show/" --confidence 0.7
```

**Guidelines:**
- Start with 0.8 (default)
- Increase if getting false matches
- Decrease if missing obvious matches
- Range: 0.0-1.0

#### Multi-Segment Analysis

v1.0.0 uses enhanced matching strategy:
- **Primary checkpoints**: 15%, 50%, 85% through video
- **Fallback checkpoints**: 25%, 35%, 65%, 75%
- **Smart termination**: Stops at first confident match
- **Empty segment handling**: Automatic fallback to additional segments

## 🖥️ Interface Tips

### GUI Mode Best Practices

**First-Time Setup:**
1. Launch: `mkv-match gui`
2. Configure settings (⚙️ icon) before processing
3. Test with dry run on small folder first
4. Use folder picker for easy navigation

**Efficient Workflow:**
1. Configure API keys once
2. Select library/show folder
3. Enable "Get Subtitles" for automatic downloads
4. Use dry run to preview changes
5. Process entire library in one operation

### CLI Mode Best Practices

**Interactive Configuration:**
```bash
# One-time setup
mkv-match config

# Verify configuration  
mkv-match config --show
```

**Production Usage:**
```bash
# Process with progress tracking
mkv-match match "/path/to/library/" --get-subs --verbose

# JSON output for automation
mkv-match match "/path/to/library/" --json > results.json

# Copy instead of rename
mkv-match match "/path/to/show/" --output-dir "/processed/"
```

## 🔧 Advanced Usage

### Testing and Validation

**Always dry run first:**
```bash
# Preview changes without modifying files
mkv-match match "/path/to/show/" --dry-run
```

**Staged processing:**
```bash
# Test on single season first
mkv-match match "/path/to/Show/Season 1/" --dry-run

# Process season after validation
mkv-match match "/path/to/Show/Season 1/" --get-subs

# Scale to full show
mkv-match match "/path/to/Show/" --get-subs
```

### Automation and Scripting

**Batch processing multiple shows:**
```bash
#!/bin/bash
for show in "/media/TV Shows"/*/; do
    echo "Processing: $show"
    mkv-match match "$show" --get-subs --confidence 0.85
done
```

**JSON output for integration:**
```bash
# Process and capture results
mkv-match match "/path/to/show/" --json > results.json

# Parse results with jq
jq '.[] | select(.confidence > 0.9)' results.json
```

### Debug and Logging

**Verbose output:**
```bash
# Detailed processing information
mkv-match match "/path/to/show/" --verbose

# Debug mode (even more detail)
mkv-match match "/path/to/show/" --verbose --confidence 0.7
```

**Log locations:**
```
~/.mkv-episode-matcher/
├── logs/
│   ├── application.log    # General operations
│   └── errors.log         # Error details
├── cache/                 # Model and data cache
└── config.json           # User configuration
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Performance Issues

**Slow Processing:**
1. ✅ Use batch processing (process folders, not individual files)
2. ✅ Enable GPU acceleration if available
3. ✅ Ensure sufficient RAM (8GB+ recommended)
4. ✅ Check disk space (5GB+ for model cache)

**Model Loading Delays:**
- First run takes longer (downloads models)
- Subsequent runs are faster (cached models)
- GPU significantly faster than CPU

#### Matching Issues

**No Matches Found:**
1. Check subtitle availability: `--get-subs`
2. Lower confidence threshold: `--confidence 0.7`
3. Verify file structure matches expected pattern
4. Review logs for specific error details

**False Matches:**
1. Increase confidence threshold: `--confidence 0.9`
2. Check subtitle quality/language
3. Verify show name detection
4. Use dry run to validate before processing

**Already Processed Files:**
- Files with S##E## patterns are automatically skipped
- Use `--force` flag to reprocess if needed
- Check logs for skip notifications

#### Configuration Problems

**API Key Issues:**
```bash
# Test OpenSubtitles connection
mkv-match config --opensub-api-key "test_key"

# Verify TMDb connectivity
mkv-match config --tmdb-api-key "test_key"
```

**Permission Errors:**
```bash
# Check file permissions
ls -la "/path/to/videos/"

# Fix ownership if needed
sudo chown -R $USER:$GROUP "/path/to/videos/"
```

**Cache Issues:**
```bash
# Clear cache and restart
rm -rf ~/.mkv-episode-matcher/cache/
mkv-match config --show
```

### Performance Benchmarks

Typical processing times (per episode):

| Setup | Audio Extraction | Speech Recognition | Matching | Total |
|-------|------------------|--------------------|---------:|------:|
| **CPU (Intel i7)** | 10-15s | 60-90s | 2-5s | ~80-110s |
| **GPU (RTX 3060)** | 10-15s | 8-15s | 2-5s | ~20-35s |
| **Apple M2 Pro** | 8-12s | 25-40s | 2-5s | ~35-55s |

**Optimization impact:**
- **Batch processing**: 10x improvement (avoids model reloads)
- **GPU acceleration**: 5-8x faster speech recognition
- **Caching**: Near-instant for repeated operations

### Getting Help

**Before reporting issues:**
1. Check existing documentation and FAQ
2. Review log files for error details
3. Test with verbose output enabled
4. Try different confidence thresholds

**Bug reports should include:**
- Operating system and version
- GPU info (if using CUDA)
- Full command and flags used
- Complete error message/traceback
- Relevant log file contents
- Sample file names (anonymized)

**Community resources:**
- [GitHub Discussions](https://github.com/Jsakkos/mkv-episode-matcher/discussions) for questions
- [GitHub Issues](https://github.com/Jsakkos/mkv-episode-matcher/issues) for bugs
- [Documentation](https://jsakkos.github.io/mkv-episode-matcher/) for guides