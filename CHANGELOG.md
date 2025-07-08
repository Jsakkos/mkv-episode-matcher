# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.3] - 2025-07-07

### Added
- Onboarding flag (`--onboard`) and interactive onboarding sequence for first-time setup and configuration updates
- Onboarding prompts for TMDb API key, OpenSubtitles API key, Consumer Name, Username, Password, and Show Directory
- Existing config values are shown as defaults during onboarding and can be accepted or overwritten
- Documentation updated to reflect onboarding requirements and workflow in README and docs

### Changed
- Improved configuration experience for new and returning users
- Quick Start and Configuration documentation now reference onboarding and required credentials

## [0.9.0] - 2025-06-01

### Changed
- Replaced all `os.path` calls with `pathlib.Path` for improved path handling
- Fixed issues with trailing slashes in directory paths
- Updated `check_filename` to handle both string paths and Path objects
- Modernized file and directory operations to use pathlib API

### Enhanced
- Improved robustness of path manipulation operations
- Better handling of different path formats across operating systems
- More consistent behavior with paths containing trailing slashes

### Fixed
- Fixed bug where paths with trailing slashes would result in empty show names
- Fixed incorrect handling of paths in subtitle downloads and match operations

## [0.7.0] - 2025-03-05

### Added
- Rich UI with color-coded output and progress indicators
- Interactive season selection interface
- Visual confirmation panels for operations
- GPU support check command
- Masked API key display for improved security
- Verbose output option for detailed logging

### Changed
- Enhanced CLI interface with better visual feedback
- Improved error messages with color coding
- Updated documentation to reflect new UI features

## [0.6.0] - 2025-03-02

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

[0.7.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.7.0
[0.6.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.6.0
[0.5.0]: https://github.com/Jsakkos/mkv-episode-matcher/releases/tag/v0.5.0
