# Configuration Guide

MKV Episode Matcher v1.0.0 supports both interactive configuration through the GUI and CLI, as well as manual JSON configuration files.

## Configuration File

MKV Episode Matcher uses a JSON configuration file located at:

- Windows: `%USERPROFILE%\.mkv-episode-matcher\config.json`
- Linux/Mac: `~/.mkv-episode-matcher/config.json`

## Configuration Methods

### 🖥️ GUI Configuration (Recommended)

The easiest way to configure the application:

1. Launch the desktop app: `mkv-match gui`
2. Click the settings (⚙️) icon in the header
3. Fill in your API keys and preferences
4. Save the configuration

The GUI provides:
- Visual input validation
- Secure password fields
- Real-time configuration testing
- Theme-adaptive settings dialog

### 💻 CLI Configuration

Interactive configuration wizard:

```bash
# Interactive setup
mkv-match config

# Set specific values
mkv-match config --tmdb-api-key "your_key" --opensub-api-key "your_key"

# Show current configuration
mkv-match config --show
```

### ✏️ Manual Configuration

Example configuration file (`config.json`):

```json
{
  "tmdb_api_key": "your_tmdb_api_key",
  "open_subtitles_api_key": "your_opensubs_key",
  "open_subtitles_user_agent": "mkv-episode-matcher/1.0.0",
  "open_subtitles_username": "your_username",
  "open_subtitles_password": "your_password",
  "cache_dir": "~/.mkv-episode-matcher/cache",
  "min_confidence": 0.8,
  "asr_provider": "parakeet",
  "sub_provider": "opensubtitles"
}
```

## Configuration Options

| Setting                    | Description                           | Default                        | Required |
| -------------------------- | ------------------------------------- | ------------------------------ | -------- |
| `tmdb_api_key`             | TMDb API key                          | None                           | No       |
| `open_subtitles_api_key`   | OpenSubtitles API key                 | None                           | Yes*     |
| `open_subtitles_user_agent`| User agent for API requests           | `mkv-episode-matcher/1.0.0`    | No       |
| `open_subtitles_username`  | OpenSubtitles username                | None                           | No†      |
| `open_subtitles_password`  | OpenSubtitles password                | None                           | No†      |
| `cache_dir`                | Cache directory path                  | `~/.mkv-episode-matcher/cache` | No       |
| `min_confidence`           | Minimum confidence threshold (0-1)    | 0.8                            | No       |
| `asr_provider`             | Speech recognition provider           | `parakeet`                     | No       |
| `sub_provider`             | Subtitle provider                     | `opensubtitles`                | No       |

\* Required if using subtitle download functionality  
† Recommended for better rate limits

## API Keys Setup

### 🎬 TMDb API Key (Optional)

TMDb integration provides enhanced episode metadata:

1. Visit [TMDb API Settings](https://www.themoviedb.org/settings/api)
2. Create a new API key
3. Add it to your configuration

**Features enabled:**
- Enhanced show identification
- Episode titles and metadata
- Season information validation

### 📥 OpenSubtitles API Key (Required for subtitles)

OpenSubtitles integration provides subtitle downloads:

1. Visit [OpenSubtitles Developers](https://www.opensubtitles.com/consumers)
2. Create an account and register an application
3. Get your API key
4. Add credentials to configuration

**Username/Password Benefits:**
- Higher API rate limits
- Better download quotas
- Priority support

## Advanced Settings

### ASR Provider Configuration

```json
{
  "asr_provider": "parakeet",
  "asr_model": "nvidia/parakeet-tdt-1.1b",
  "asr_device": "auto"
}
```

**Available providers:**
- `parakeet`: NVIDIA Parakeet (default, most accurate)
- `whisper`: OpenAI Whisper (fallback)

### Cache Configuration

```json
{
  "cache_dir": "/custom/cache/path",
  "cache_max_memory_mb": 512,
  "cache_max_items": 100
}
```

**Cache features:**
- Bounded memory usage (512MB default)
- LRU eviction strategy
- Persistent model caching

### Network Configuration

```json
{
  "network_timeout": 30,
  "network_retries": 3,
  "backoff_factor": 2.0
}
```

**Network resilience:**
- Automatic retries with exponential backoff
- Configurable timeouts
- Connection error handling

## Configuration Validation

The application validates configuration on startup:

✅ **Valid Configuration:**
- All required keys present
- API keys have correct format
- Paths are accessible
- Values within valid ranges

❌ **Common Issues:**
- Missing OpenSubtitles API key when using `--get-subs`
- Invalid cache directory permissions
- Confidence threshold outside 0.0-1.0 range

## Environment Variables

Override configuration with environment variables:

```bash
export MKV_TMDB_API_KEY="your_key"
export MKV_OPENSUB_API_KEY="your_key"
export MKV_CACHE_DIR="/custom/cache"
export MKV_CONFIDENCE=0.85

mkv-match match "/path/to/show/"
```

## Troubleshooting

### Configuration Not Found

If configuration is missing:
1. Run `mkv-match config` to create it
2. Or use GUI settings to initialize
3. Check file permissions in `~/.mkv-episode-matcher/`

### API Key Issues

For API authentication problems:
1. Verify keys in your provider dashboards
2. Check network connectivity
3. Review rate limiting messages in logs

### Permission Errors

For cache directory issues:
1. Ensure write permissions to cache directory
2. Try custom cache directory: `--cache-dir "/writable/path"`
3. Check disk space availability
