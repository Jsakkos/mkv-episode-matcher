# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-27 - Major Release 🎉

### 🖥️ Added - Desktop GUI
- **Complete Flet-based desktop application** with cross-platform support
- **Theme-adaptive interface** that follows system light/dark mode
- **Real-time progress tracking** with "Processing file X of Y" indicators
- **Background model loading** with status indicators to prevent UI freezing
- **Built-in configuration dialog** accessible via settings icon
- **Dry run preview mode** allowing users to preview rename operations
- **Visual folder picker** for easy directory selection
- **Color-coded results display** with detailed match information and confidence scores
- **Responsive progress bars and status indicators**
- **Version display and model loading status in app header**

### 🤖 Enhanced - ASR and Matching Engine
- **Complete rewrite of matching engine (V2)** with improved architecture
- **NVIDIA Parakeet ASR integration** replacing OpenAI Whisper for better accuracy
- **Multi-segment analysis with fallback strategies** to handle empty transcription segments
- **Enhanced caching system** for performance optimization
- **Intelligent checkpoint selection** with primary and fallback locations
- **Improved confidence scoring and voting logic**
- **Better error handling for silent/music-only video segments**

### 📊 Improved - Core Processing
- **Automatic series and season detection** from directory structure
- **Enhanced subtitle provider system** with local caching and OpenSubtitles integration
- **Optimized file processing workflow** with progress callbacks
- **Smart skip logic** for already processed files with S##E## patterns
- **Better failure reporting** with season information for user guidance
- **Comprehensive error handling** with user-friendly messages

### ⚡ Performance Optimizations
- **Model singleton pattern** to avoid repeated ASR model loading
- **Memory caching** for subtitle content and metadata
- **Background task processing** for non-blocking operations  
- **Efficient file scanning** with recursive directory support
- **LRU caching** for video duration and metadata

### 🛠️ Technical Improvements
- **Complete code restructuring** with core/, ui/, and providers/ modules
- **Pydantic models** for type safety and validation
- **Modern async/await patterns** for GUI responsiveness
- **Enhanced logging** with structured debug information
- **Improved configuration management** with centralized config system
- **Better path handling** using pathlib throughout

### 🎨 User Experience
- **Comprehensive onboarding process** for first-time setup
- **Interactive configuration with validation** 
- **Rich console output** with color coding and progress indicators
- **Detailed match results** with confidence percentages
- **Preview functionality** to test matches before applying changes
- **Better error messages** with actionable guidance

### 🚀 Deployment Ready
- **Flet build configuration** for Windows, macOS, and Linux executables
- **GitHub Actions ready** for automated builds and releases
- **Comprehensive packaging** with all required dependencies
- **Cross-platform compatibility** testing

### 🔧 Developer Experience  
- **Modular architecture** with clear separation of concerns
- **Comprehensive type hints** throughout the codebase
- **Enhanced test coverage** with pytest and mocking
- **Ruff formatting and linting** configuration
- **Documentation updates** reflecting new architecture

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
