# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests with coverage
uv run pytest --cov=mkv_episode_matcher --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_main.py -v

# Run tests in verbose mode
uv run pytest -v
```

### Linting and Formatting
```bash
# Run ruff linting
uv run ruff check .

# Run ruff formatting
uv run ruff format .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Dependency Management and Installation
```bash
# Install dependencies
uv sync

# Install with dev dependencies (default behavior)
uv sync --group dev

# Add new dependency
uv add package-name

# Add dev dependency
uv add --group dev package-name

# Install in editable mode for development
uv sync --editable

# Build distribution packages
uv build
```

### Running the Application
```bash
# Run onboarding (first time setup)
mkv-match --onboard

# Process a show directory
mkv-match --show-dir "/path/to/show"

# Dry run mode (test without making changes)
mkv-match --show-dir "/path/to/show" --dry-run

# Process specific season
mkv-match --show-dir "/path/to/show" --season 1

# Download subtitles and process
mkv-match --show-dir "/path/to/show" --get-subs
```

## Architecture Overview

### Core Components

**Main Entry Point** (`__main__.py`):
- CLI argument parsing and rich console interface
- Configuration management and onboarding flow
- Coordinates the overall process execution

**Episode Matcher** (`episode_matcher.py`):
- High-level orchestration of the matching process
- Progress tracking and user feedback
- Handles season/episode file processing workflow

**Episode Identification** (`episode_identification.py`):
- Core speech recognition using OpenAI Whisper
- Subtitle comparison and matching algorithms
- Audio extraction and processing with FFmpeg
- Caching systems for performance optimization

**Configuration System** (`config.py`):
- INI-based configuration management
- API key and credential storage
- Show directory and user preferences

**Utilities** (`utils.py`):
- File operations (renaming, validation)
- Text processing and cleaning
- Season/episode extraction from filenames

### Dependencies

**Required External Tools**:
- FFmpeg (for audio extraction from MKV files)
- Python 3.9-3.12

**Key Python Dependencies**:
- OpenAI Whisper (speech recognition)
- TMDb Client (show metadata)
- OpenSubtitles API (subtitle downloads)
- Rich (CLI interface)
- RapidFuzz (text matching)
- PyTorch (Whisper backend)

### Data Flow

1. **Configuration**: Load user settings, API keys, and show directory
2. **File Discovery**: Find MKV files in season directories
3. **Audio Extraction**: Extract audio chunks from MKV files using FFmpeg
4. **Speech Recognition**: Use Whisper to transcribe audio chunks
5. **Subtitle Matching**: Compare transcriptions with reference subtitles
6. **File Renaming**: Rename files based on identified episodes

### Caching Strategy

- **Whisper Models**: Cached globally to avoid reloading
- **Audio Chunks**: Temporary files cached during processing
- **Reference Subtitles**: Parsed subtitle content cached per session
- **Video Duration**: FFprobe results cached with LRU cache

### Configuration Files

- **Config Location**: `~/.mkv-episode-matcher/config.ini`
- **Cache Directory**: `~/.mkv-episode-matcher/cache/`
- **Logs Directory**: `~/.mkv-episode-matcher/logs/`

### Testing Strategy

- Uses pytest with fixtures for mock data
- Coverage reporting configured via pytest-cov
- Test files follow `test_*.py` naming convention
- Mocks external dependencies (TMDb API, file operations)

### Code Quality

- Ruff for linting and formatting
- Type hints where applicable
- Comprehensive error handling and logging
- Rich console output for user experience