"""MKV Episode Matcher package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mkv-episode-matcher")
except PackageNotFoundError:
    # package is not installed, use hardcoded version
    __version__ = "1.2.0"

