# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2025-02-24

### Added
- Comprehensive documentation including installation, configuration, and CLI guides
- Quick start guide with common usage examples
- Tips and tricks documentation with best practices
- Detailed changelog structure

### Changed
- Improved project metadata and description
- Updated version number in setup.cfg

### Removed
- Removed OCR support and Tesseract dependency
- Removed unused code

## [0.5.0] - 2025-02-23

### Changed
- Try to use tiny version of OpenAI Whisper for initial matching
- Fall back to base model if tiny model fails
- Progressive matching in 30s intervals (was 300s)

### Removed
- Removed unused code

[0.6.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.6.0
[0.5.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.5.0
