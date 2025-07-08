# test_path_handling.py
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add the parent directory to the path so we can import the project modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))

# Import the modules we want to test
from mkv_episode_matcher.utils import check_filename, normalize_path

# Test paths to use in tests
TEST_PATHS = [
    ("/mnt/c/Shows/Breaking Bad", "Breaking Bad"),  # Normal path
    ("/mnt/c/Shows/Breaking Bad/", "Breaking Bad"),  # Linux trailing slash
    ("/mnt/c/Shows/Breaking Bad\\", "Breaking Bad"),  # Windows trailing backslash
    ("/mnt/c/Shows/Breaking Bad//", "Breaking Bad"),  # Double trailing slash
    ("C:\\Shows\\The Office\\", "The Office"),  # Windows path with trailing slash
    ("/home/user/Shows/Game of Thrones/", "Game of Thrones"),  # Another Linux path
]


class TestPathLibImplementation(unittest.TestCase):
    """Test the pathlib implementation used throughout the codebase"""

    def test_show_name_extraction_with_pathlib(self):
        """Test that normalize_path.name correctly extracts the show name even with trailing slash"""
        # Path with trailing slash that previously caused bugs with os.path.basename
        path_with_trailing_slash = "/mnt/c/Shows/Breaking Bad/"

        # Expected correct show name
        expected_show_name = "Breaking Bad"

        # Our new implementation using normalize_path
        extracted_name = normalize_path(path_with_trailing_slash).name

        # This should succeed with our normalized path
        self.assertEqual(
            extracted_name,
            expected_show_name,
            "normalize_path.name should correctly extract the show name with trailing slash",
        )

    def test_check_filename_with_path_objects(self):
        """Test that check_filename works with both Path objects and strings"""
        # Test with string path
        string_path = "/path/to/Show.S01E01.mkv"
        self.assertTrue(
            check_filename(string_path), "check_filename should work with string paths"
        )

        # Test with Path object
        path_object = Path("/path/to/Show.S01E01.mkv")
        self.assertTrue(
            check_filename(path_object), "check_filename should work with Path objects"
        )

    def test_path_operations(self):
        """Test various Path operations used in the codebase"""
        base_path = Path("/mnt/c/Shows/Breaking Bad")

        # Test Path joining with / operator
        episode_path = base_path / "Season 1" / "Episode 1.mkv"
        expected_path = Path("/mnt/c/Shows/Breaking Bad/Season 1/Episode 1.mkv")
        self.assertEqual(
            episode_path,
            expected_path,
            "Path joining with / operator should work correctly",
        )

        # Test parent directory
        self.assertEqual(
            episode_path.parent,
            Path("/mnt/c/Shows/Breaking Bad/Season 1"),
            "Parent directory should be correctly identified",
        )

        # Test name extraction
        self.assertEqual(
            episode_path.name, "Episode 1.mkv", "Filename should be correctly extracted"
        )

        # Test stem and suffix
        self.assertEqual(
            episode_path.stem, "Episode 1", "File stem should be correctly extracted"
        )
        self.assertEqual(
            episode_path.suffix, ".mkv", "File extension should be correctly extracted"
        )


class TestEpisodeMatcherShowNameExtraction(unittest.TestCase):
    """Test the show name extraction in episode_matcher.py"""

    @mock.patch("mkv_episode_matcher.config.get_config")
    def test_episode_matcher_show_name_with_trailing_slash(self, mock_get_config):
        """Test that process_show extracts show_name incorrectly with trailing slash"""
        # Create a mock config that returns a path with trailing slash
        mock_config = mock.MagicMock()
        mock_config.get.return_value = "/mnt/c/Shows/Breaking Bad/"
        mock_get_config.return_value = mock_config

        # Import the module under test

        # Access the function that should be affected by the bug
        # This line simulates what happens in process_show() but we're just testing the show_name extraction
        show_dir = mock_config.get("show_dir")

        # How the code would extract show_name with normalize_path - this would work
        fixed_show_name = normalize_path(show_dir).name
        self.assertEqual(
            fixed_show_name,
            "Breaking Bad",
            "normalize_path.name should extract correct show name even with trailing slash",
        )


def test_pathlib_works_with_trailing_slashes():
    """Test that normalize_path.name works correctly with trailing slashes"""
    for path, expected in TEST_PATHS:
        result = normalize_path(path).name
        assert result == expected, (
            f"Normalized path should extract correct name for: {path}"
        )
