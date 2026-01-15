# Changelog

All notable changes to MKV Episode Matcher are documented here.

> [!TIP]
> For the complete changelog history, see [CHANGELOG.md](https://github.com/Jsakkos/mkv-episode-matcher/blob/main/CHANGELOG.md) in the repository.

## [1.1.0] - 2026-01-11 - Polish Release ✨

### 🖥️ UI/UX Improvements
- **Complete Redesign**: New glassmorphism-inspired UI with modern color palette and improved aesthetics
- **Enhanced Workflow**: Clearer 4-step process (Folder Selection → Scan → Review → Match)
- **Component Refactoring**: Cleaner code structure with explicit Sidebar and Layout components
- **System Status Indicator**: Prominent indicator for backend system and model loading status

### ⚡ Backend Optimizations
- **Singleton Model Loading**: Fixed issue where Parakeet model was loaded multiple times
- **Background Loading**: Model initialization now happens in background on startup
- **Status Endpoint**: New `/system/status` endpoint for frontend health checks
- **Performance**: Significant reduction in resource usage during repeated scans

### 🛠️ Fixes & Updates
- **Dependency Updates**: Relaxed Python version constraints
- **CLI improvements**: Better error handling and help output
- **Documentation**: Updated CLI and README documentation

---

## [1.0.0] - Major Release

### 🖥️ Desktop GUI
- **Complete Flet-based desktop application** with cross-platform support
- **Theme-adaptive interface** that follows system light/dark mode
- **Real-time progress tracking** with "Processing file X of Y" indicators
- **Background model loading** with status indicators to prevent UI freezing
- **Built-in configuration dialog** accessible via settings icon
- **Dry run preview mode** allowing users to preview rename operations
- **Visual folder picker** for easy directory selection
- **Color-coded results display** with detailed match information and confidence scores

### 🤖 Enhanced ASR and Matching Engine
- **Complete rewrite of matching engine (V2)** with improved architecture
- **NVIDIA Parakeet ASR integration** replacing OpenAI Whisper for better accuracy
- **Multi-segment analysis with fallback strategies** to handle empty transcription segments
- **Enhanced caching system** for performance optimization
- **Intelligent checkpoint selection** with primary and fallback locations
- **Improved confidence scoring and voting logic**

### 📊 Improved Core Processing
- **Automatic series and season detection** from directory structure
- **Enhanced subtitle provider system** with local caching and OpenSubtitles integration
- **Optimized file processing workflow** with progress callbacks
- **Smart skip logic** for already processed files with S##E## patterns
- **Comprehensive error handling** with user-friendly messages

### ⚡ Performance Optimizations
- **Model singleton pattern** to avoid repeated ASR model loading
- **Memory caching** for subtitle content and metadata
- **Background task processing** for non-blocking operations
- **Efficient file scanning** with recursive directory support
- **LRU caching** for video duration and metadata

> [!IMPORTANT]
> First run takes **~60 seconds** to download and initialize the NVIDIA Parakeet ASR model.

---

## Previous Versions

### [0.9.3] - 2025-07-07
- Onboarding flag (`--onboard`) and interactive onboarding sequence for first-time setup
- Improved configuration experience for new and returning users

### [0.9.0] - 2025-06-01
- Replaced all `os.path` calls with `pathlib.Path` for improved path handling
- Fixed issues with trailing slashes in directory paths

### [0.7.0] - 2025-03-05
- Rich UI with color-coded output and progress indicators
- Interactive season selection interface
- GPU support check command

### [0.6.0] - 2025-03-02
- Comprehensive documentation including installation, configuration, and CLI guides
- Quick start guide with common usage examples

### [0.5.0] - 2025-02-23
- Progressive matching in 30s intervals (was 300s)

---

[View full changelog on GitHub](https://github.com/Jsakkos/mkv-episode-matcher/releases)
