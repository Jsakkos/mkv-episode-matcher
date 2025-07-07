# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MKV Episode Matcher is a Python CLI tool that automatically matches and renames MKV TV episodes using The Movie Database (TMDb) API. The tool uses speech recognition (Whisper) to identify episodes by analyzing audio from MKV files and comparing against reference subtitles.

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

- **`__main__.py`**: Entry point with rich CLI interface, argument parsing, and configuration management
- **`episode_matcher.py`**: Core processing logic that orchestrates the matching workflow
- **`episode_identification.py`**: Contains the `EpisodeMatcher` class that handles speech recognition and subtitle comparison
- **`tmdb_client.py`**: TMDb API client for fetching show metadata
- **`subtitle_utils.py`**: Subtitle extraction and processing utilities
- **`utils.py`**: General utility functions for file operations and text processing
- **`config.py`**: Configuration management for API keys and settings

## Key Dependencies

- **OpenAI Whisper**: For speech recognition from MKV audio tracks
- **TMDb API**: For show metadata and episode information
- **OpenSubtitles API**: For downloading reference subtitles
- **Rich**: For enhanced CLI interface with progress bars and colored output
- **FFmpeg**: External dependency for audio/video processing
- **PyTorch**: Required for Whisper model execution

## Development Commands

### Setup and Installation
```bash
pip install -e .                    # Install in development mode
pip install -e ".[dev]"            # Install with development dependencies
```

### Code Quality
```bash
ruff check                          # Run linter
ruff format                         # Format code
ruff check --fix                    # Auto-fix linting issues
```

### Testing
```bash
pytest                              # Run all tests
pytest tests/test_main.py          # Run specific test file
pytest --cov=mkv_episode_matcher   # Run with coverage
```

### Building
```bash
python -m build                     # Build distribution packages
```

## Configuration

The tool uses a configuration file at `~/.mkv-episode-matcher/config.ini` to store:
- TMDb API key
- OpenSubtitles credentials
- Default show directory
- User preferences

Reference subtitle files are stored at `~/.mkv-episode-matcher/cache/data/{show_name}/` following the pattern: `{show_name} - S{season:02d}E{episode:02d}.srt`

## Core Workflow

1. **Configuration**: Load user settings and API keys
2. **Season Detection**: Scan show directory for seasons with MKV files
3. **Audio Extraction**: Use FFmpeg to extract audio from MKV files
4. **Speech Recognition**: Process audio with Whisper to generate transcripts
5. **Subtitle Matching**: Compare transcripts against reference subtitles using fuzzy matching
6. **Episode Identification**: Determine episode number based on best match
7. **File Renaming**: Rename MKV files to standardized format

## Important Notes

- The tool expects show directories organized as `Show Name/Season X/episode.mkv`
- Reference subtitles are crucial for accurate matching - either provide them manually or use `--get-subs` flag
- GPU support is available for faster Whisper processing
- The tool includes extensive logging to `~/.mkv-episode-matcher/logs/`
- Dry run mode (`--dry-run`) allows testing without actual file modifications

## API Integration

- **TMDb API**: Used for show metadata and episode information
- **OpenSubtitles API**: Used for downloading reference subtitles when `--get-subs` is enabled
- Rate limiting and retry mechanisms are implemented for both APIs