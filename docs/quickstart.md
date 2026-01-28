# Quick Start Guide

Get started with MKV Episode Matcher quickly and efficiently.

## 🚀 Launch the Application

### Option 1: Windows Executable (Recommended)
The easiest way to run the application on Windows is using the standalone executable.

1.  Download `mkv-match.exe` from **[GitHub Releases](https://github.com/Jsakkos/mkv-episode-matcher/releases)**.
2.  Double-click `mkv-match.exe`.
3.  The Web UI will open automatically in your browser.

> [!NOTE]
> First run takes **~5-10 seconds** to load the speech recognition model. You will see a "System Loading" indicator.

### Option 2: Python / Command Line
If you installed via pip or are running from source:

```bash
# Launch the web interface (opens http://localhost:8001)
mkv-match serve

# Or use the gui alias
mkv-match gui
```

## 📸 Web UI Onboarding

**Dashboard - Select Your Media Folder**
![MKV Matcher Dashboard showing file browser](images/web_ui_dashboard.png)

**Settings - Configure API Keys**
![Settings page with OpenSubtitles and TMDb configuration](images/web_ui_settings.png)

## First Time Setup

1. **Start the App**: Launch `mkv-match.exe` or run `mkv-match serve`.
2. **Configure Settings**:
   - Go to the **Settings** tab.
   - Enter your **OpenSubtitles** credentials (for subtitles).
   - Enter your **TMDb API Key** (for reliable titles).
   - Click **Save**.
3. **Select a Folder**:
   - Go to the **Dashboard**.
   - Navigate to your TV show folder.
   - *Ensure your files are organized by Show/Season (see [Directory Structure](#directory-structure)).*
4. **Scan and Match**:
   - Click **"Scan This Folder"**.
   - Review the proposed matches.
   - Click **"Rename Files"** to apply changes.

## 💻 Command Line Interface (Advanced)

For automation and advanced users who prefer the terminal.

### 1. Configuration Setup
```bash
# Interactive configuration wizard
mkv-match config

# Set specific configuration values
mkv-match config --tmdb-api-key "your_key" --opensub-api-key "your_key"
```

### 2. Basic Matching
```bash
# Process a single MKV file
mkv-match match "/path/to/episode.mkv"

# Process an entire series folder
mkv-match match "/path/to/Show/Season 1/"

# Process entire library with subtitle downloads
mkv-match match "/path/to/library/" --get-subs
```

### 3. Advanced Options
```bash
# Dry run with specific season
mkv-match match "/path/to/show/" --season 1 --dry-run

# JSON output for automation
mkv-match match "/path/to/show/" --json

# Copy files instead of renaming
mkv-match match "/path/to/show/" --output-dir "/path/to/renamed/"
```

## ⚡ Performance Tips

### Batch Processing
**Important:** The ASR model takes time to initialize. For best performance:

✅ **DO:** Process entire folders/seasons at once
```bash
# Process whole season - model loads once for all files
mkv-match match "/path/to/Show/Season 1/"
```

❌ **DON'T:** Process files one by one
```bash
# Inefficient - model reloads for each file
mkv-match match "/path/to/episode1.mkv"
mkv-match match "/path/to/episode2.mkv"
```

## 📁 Directory Structure

Expected TV show organization:
```
Media Library/
├── Show Name/
│   ├── Season 1/
│   │   ├── episode1.mkv
│   │   ├── episode2.mkv
│   └── Season 2/
│       ├── episode1.mkv
│       └── episode2.mkv
```

## 📚 Next Steps

- Read [Installation Guide](installation.md) for detailed setup options.
- Check [CLI Reference](cli.md) for full command documentation.
- Visit [Configuration Guide](configuration.md) for advanced settings.
