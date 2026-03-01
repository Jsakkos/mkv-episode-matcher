# Frontend Build Instructions

This document explains how to build the frontend assets for the MKV Episode Matcher web interface.

## Automatic Build (Recommended)

The frontend is automatically built during package installation via UV or pip. The setup.py includes a custom build command that:

1. Detects if Node.js and npm are available
2. Installs frontend dependencies
3. Builds the frontend assets
4. Creates placeholder assets if the build fails

No manual action is required in most cases.

## Manual Build

If you need to build the frontend manually:

### Prerequisites

- Node.js (v16 or later)
- npm

### Steps

```bash
# Navigate to the frontend directory
cd mkv_episode_matcher/frontend

# Install dependencies
npm install

# Build the frontend
npm run build
```

This will create the `dist/assets/` directory with the compiled CSS and JavaScript files.

## Troubleshooting

### Missing Assets Error

If you see errors like:
```
RuntimeError: Directory '/path/to/mkv_episode_matcher/frontend/dist/assets' does not exist
```

This means the frontend assets weren't built. Try:

1. Manual build (see steps above)
2. Reinstall the package: `uv sync` or `pip install -e .`

### 404 Errors in Browser

If you see 404 errors for CSS/JS files, the frontend build may have failed. Check:

1. Node.js is installed: `node --version`
2. Build manually as described above
3. Check the browser network tab for specific missing files

### Build Fails

If the build fails:

1. Ensure Node.js v16+ is installed
2. Clear node_modules: `rm -rf node_modules && npm install`
3. Check for TypeScript errors: `npm run build` (verbose output)

## Development

For frontend development:

```bash
cd mkv_episode_matcher/frontend
npm run dev  # Start development server
npm run lint # Run ESLint
```