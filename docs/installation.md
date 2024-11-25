# Installation Guide

## Basic Installation

Install MKV Episode Matcher using pip:

```bash
pip install mkv-episode-matcher
```

## API Keys Setup

1. **TMDb API Key**
    - Create an account at [TMDb](https://www.themoviedb.org/)
    - Go to your account settings
    - Request an API key

2. **OpenSubtitles (Optional)**
    - Register at [OpenSubtitles](https://www.opensubtitles.com/)
    - Get your API key from the dashboard

## Development Installation

For contributing or development:

```bash
# Clone the repository
git clone https://github.com/Jsakkos/mkv-episode-matcher.git
cd mkv-episode-matcher

# Install UV
pip install uv

# Load the virtual environment
uv sync

# Install in development mode
pip install -e .
```

## Verification

Verify your installation:

```bash
mkv-match --version
```

## Troubleshooting

If you encounter any issues, please [open an issue](https://github.com/Jsakkos/mkv-episode-matcher/issues) on GitHub.
