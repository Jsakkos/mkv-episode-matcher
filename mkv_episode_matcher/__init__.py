"""MKV Episode Matcher package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mkv-episode-matcher")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"
