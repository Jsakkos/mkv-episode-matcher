# tests/test_trailing_slash.py

"""
This test verifies that pathlib.Path.name correctly handles paths with trailing slashes.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mkv_episode_matcher.utils import normalize_path

# Test paths with their expected basename
TEST_PATHS = [
    ("/mnt/c/Shows/Breaking Bad", "Breaking Bad"),  # Unix normal path
    ("/mnt/c/Shows/Breaking Bad/", "Breaking Bad"),  # Unix trailing slash
    ("X:\\Shows\\Breaking Bad", "Breaking Bad"),  # Windows normal path
    ("X:\\Shows\\Breaking Bad\\", "Breaking Bad"),  # Windows trailing backslash
]


def test_pathlib_works_with_trailing_slash():
    """Verify that pathlib.Path.name correctly handles paths with trailing slash."""
    path_with_slash = "/mnt/c/Shows/Breaking Bad/"
    result = normalize_path(path_with_slash).name
    assert result == "Breaking Bad", (
        "Path.name should extract correct name even with trailing slash"
    )


def test_pathlib_works_with_trailing_backslash():
    """Verify that pathlib.Path.name correctly handles paths with trailing backslash."""
    path_with_backslash = "X:\\Shows\\Breaking Bad\\"
    result = normalize_path(path_with_backslash).name
    assert result == "Breaking Bad", (
        "Path.name should extract correct name even with trailing backslash"
    )


def test_pathlib_works_without_trailing_slash():
    """Verify pathlib works correctly for paths without trailing slash."""
    normal_path = "/mnt/c/Shows/Breaking Bad"
    result = normalize_path(normal_path).name
    assert result == "Breaking Bad", (
        "Path.name should work for paths without trailing slash"
    )


def test_path_parent_behavior():
    """Test that Path.parent correctly handles paths with trailing slashes."""
    path_with_slash = "/mnt/c/Shows/Breaking Bad/"
    path_without_slash = "/mnt/c/Shows/Breaking Bad"

    assert normalize_path(path_with_slash).parent == Path("/mnt/c/Shows"), (
        "Parent should be correctly extracted"
    )
    assert normalize_path(path_without_slash).parent == Path("/mnt/c/Shows"), (
        "Parent should be correctly extracted"
    )


def test_path_stem_suffix():
    """Test Path.stem and Path.suffix functionality."""
    path = "/mnt/c/Shows/Breaking Bad/episode.mkv"
    path_obj = Path(path)

    assert path_obj.stem == "episode", "Stem should be correctly extracted"
    assert path_obj.suffix == ".mkv", "Suffix should be correctly extracted"


def test_all_paths_with_pathlib():
    """Test all the path formats with pathlib."""
    for path, expected in TEST_PATHS:
        # Check normalize_path.name always works
        pathlib_result = normalize_path(path).name
        assert pathlib_result == expected, (
            f"Expected '{expected}' for normalize_path('{path}').name but got '{pathlib_result}'"
        )
        rstrip_result = normalize_path(path).name
        assert rstrip_result == expected, (
            f"Expected '{expected}' for normalize_path approach on '{path}' but got '{rstrip_result}'"
        )
