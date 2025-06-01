# tests/test_trailing_slash.py

"""
This test verifies that pathlib.Path.name correctly handles paths with trailing slashes.
"""

from pathlib import Path

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
    result = Path(path_with_slash).name
    assert result == "Breaking Bad", "Path.name should extract correct name even with trailing slash"

def test_pathlib_works_with_trailing_backslash():
    """Verify that pathlib.Path.name correctly handles paths with trailing backslash."""
    path_with_backslash = "X:\\Shows\\Breaking Bad\\"
    result = Path(path_with_backslash).name
    assert result == "Breaking Bad", "Path.name should extract correct name even with trailing backslash"

def test_pathlib_works_without_trailing_slash():
    """Verify pathlib works correctly for paths without trailing slash."""
    normal_path = "/mnt/c/Shows/Breaking Bad"
    result = Path(normal_path).name
    assert result == "Breaking Bad", "Path.name should work for paths without trailing slash"

def test_path_parent_behavior():
    """Test that Path.parent correctly handles paths with trailing slashes."""
    path_with_slash = "/mnt/c/Shows/Breaking Bad/"
    path_without_slash = "/mnt/c/Shows/Breaking Bad"
    
    assert Path(path_with_slash).parent == Path("/mnt/c/Shows"), "Parent should be correctly extracted"
    assert Path(path_without_slash).parent == Path("/mnt/c/Shows"), "Parent should be correctly extracted"

def test_path_stem_suffix():
    """Test Path.stem and Path.suffix functionality."""
    path = "/mnt/c/Shows/Breaking Bad/episode.mkv"
    path_obj = Path(path)
    
    assert path_obj.stem == "episode", "Stem should be correctly extracted"
    assert path_obj.suffix == ".mkv", "Suffix should be correctly extracted"

def test_all_paths_with_pathlib():
    """Test all the path formats with pathlib."""
    for path, expected in TEST_PATHS:
        # Check Path.name always works
        pathlib_result = Path(path).name
        assert pathlib_result == expected, f"Expected '{expected}' for Path('{path}').name but got '{pathlib_result}'"
        rstrip_result = Path(path.rstrip('/').rstrip('\\')).name
        assert rstrip_result == expected, f"Expected '{expected}' for rstrip approach on '{path}' but got '{rstrip_result}'"
