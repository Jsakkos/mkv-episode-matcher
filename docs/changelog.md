# Changelog

For a complete list of changes, see [CHANGELOG.md](../CHANGELOG.md) in the repository root.

## Latest Changes

## [0.6.0] - 2025-02-25

### Changed
- Enhanced speech recognition with progressive model fallbacks (tiny → base → small)
- Extended audio matching duration to 15 minutes for difficult cases
- Improved subtitle file reading with robust encoding detection
- Simplified codebase and reduced dependencies

### Removed
- Removed OCR fallback functionality 
- Removed Tesseract OCR dependency
- Removed SUP/PGS subtitle extraction and processing
- Removed OCR-related configuration options

## [0.5.0] - 2025-02-23

### Changed
- Try to use tiny version of OpenAI Whisper for initial matching
- Fall back to base model if tiny model fails
- Progressive matching in 30s intervals (was 300s)

### Removed
- Removed unused code

[0.6.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.6.0
[0.5.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.5.0


For older versions and complete changelog history, please visit our [GitHub releases page](https://github.com/Jsakkos/mkv-episode-matcher/releases).