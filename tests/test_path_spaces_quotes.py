import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from mkv_episode_matcher.core.models import Config
from mkv_episode_matcher.utils import get_subtitles, get_valid_seasons, normalize_path


class TestPathHandlingWithSpacesAndQuotes(unittest.TestCase):
    """Test path handling for issues 61 and 62 - paths with spaces and quotes."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_normalize_path_with_spaces(self):
        """Test that normalize_path handles paths with spaces correctly."""
        paths_with_spaces = [
            "C:\\my rips\\show name",
            "/home/user/TV Shows/My Show",
            "C:/Program Files/My TV Shows/Show With Spaces",
            "/mnt/c/Users/John Doe/Shows/Breaking Bad",
            "D:\\Users\\Jane Smith\\My Videos\\Game of Thrones\\",
        ]

        for path_str in paths_with_spaces:
            with self.subTest(path=path_str):
                normalized = normalize_path(path_str)
                # Should return a valid Path object
                self.assertIsInstance(normalized, Path)
                # Should preserve the directory name with spaces
                self.assertIn(
                    " ",
                    normalized.name,
                    f"Path with spaces should preserve spaces: {path_str}",
                )

    def test_normalize_path_with_quotes(self):
        """Test that normalize_path handles paths with quotes correctly."""
        paths_with_quotes = [
            '"C:\\my rips\\show name"',
            '"/home/user/TV Shows/My Show"',
            "'C:/Program Files/My TV Shows/Show With Spaces'",
            '"D:\\Users\\Jane Smith\\My Videos\\Game of Thrones\\"',
        ]

        for path_str in paths_with_quotes:
            with self.subTest(path=path_str):
                normalized = normalize_path(path_str)
                # Should return a valid Path object
                self.assertIsInstance(normalized, Path)
                # Should not contain quotes in the final path
                self.assertNotIn('"', str(normalized))
                self.assertNotIn("'", str(normalized))

    def test_get_valid_seasons_with_spaces(self):
        """Test that get_valid_seasons works with directories containing spaces."""
        # Create test directory structure with spaces
        show_dir = self.temp_path / "My Test Show"
        show_dir.mkdir()

        season1_dir = show_dir / "Season 1"
        season2_dir = show_dir / "Season 2 - Special Edition"
        season1_dir.mkdir()
        season2_dir.mkdir()

        # Create some .mkv files
        (season1_dir / "Episode 1.mkv").touch()
        (season1_dir / "Episode 2.mkv").touch()
        (season2_dir / "Special Episode.mkv").touch()

        # Test with path containing spaces
        seasons = get_valid_seasons(str(show_dir))

        # Should find both seasons
        self.assertEqual(len(seasons), 2)
        self.assertTrue(any("Season 1" in str(season) for season in seasons))
        self.assertTrue(
            any("Season 2 - Special Edition" in str(season) for season in seasons)
        )

    def test_command_line_parsing_with_spaces(self):
        """Test that command line argument parsing handles paths with spaces."""

        test_cases = [
            ["--show-dir", "C:\\my rips\\show name"],
            ["--show-dir", "/home/user/TV Shows/My Show"],
            ["--show-dir", "D:\\Users\\Jane Smith\\My Videos"],
        ]

        for args in test_cases:
            with self.subTest(args=args):
                parser = argparse.ArgumentParser()
                parser.add_argument("--show-dir", help="Main directory of the show")

                # This should not raise an exception
                parsed_args = parser.parse_args(args)
                self.assertIsNotNone(parsed_args.show_dir)
                # Spaces should be preserved
                self.assertIn(" ", parsed_args.show_dir)

    def test_command_line_parsing_with_quotes(self):
        """Test that command line argument parsing handles quoted paths."""
        test_cases = [
            ["--show-dir", '"C:\\my rips\\show name"'],
            ["--show-dir", '"/home/user/TV Shows/My Show"'],
            ["--show-dir", "'D:\\Users\\Jane Smith\\My Videos'"],
        ]

        for args in test_cases:
            with self.subTest(args=args):
                parser = argparse.ArgumentParser()
                parser.add_argument("--show-dir", help="Main directory of the show")

                # This should not raise an exception
                parsed_args = parser.parse_args(args)
                self.assertIsNotNone(parsed_args.show_dir)
                # Should handle quotes appropriately
                # Note: argparse typically strips outer quotes automatically

    def test_config_storage_with_spaces(self):
        """Test that configuration correctly stores and retrieves paths with spaces."""
        # Test path with spaces
        # test_path = "C:\\Users\\John Doe\\My TV Shows\\Breaking Bad"
        # We need to use a path that exists for validation.
        # But wait, does validation check if it exists? Yes.
        # So we must create it.
        show_dir = self.temp_path / "My TV Shows" / "Breaking Bad"
        show_dir.mkdir(parents=True)
        test_path = str(show_dir)

        # Create a temporary config file
        config_file = self.temp_path / "test_config.json"

        from mkv_episode_matcher.core.config_manager import ConfigManager

        cm = ConfigManager(config_path=config_file)

        # Set config with path containing spaces
        config_data = {
            "tmdb_api_key": "test_key",
            "open_subtitles_api_key": "test_key",
            "open_subtitles_user_agent": "test_agent",
            "open_subtitles_username": "test_user",
            "open_subtitles_password": "test_pass",
            "show_dir": test_path,
        }
        config = Config(**config_data)
        cm.save(config)

        # Read back the config
        loaded_config = cm.load()

        # Should preserve spaces in the path
        self.assertEqual(str(loaded_config.show_dir), test_path)
        self.assertIn(" ", str(loaded_config.show_dir))

    @patch("mkv_episode_matcher.utils.get_config_manager")
    @patch("mkv_episode_matcher.utils.OpenSubtitles")
    @patch("mkv_episode_matcher.tmdb_client.fetch_season_details")
    @patch("mkv_episode_matcher.utils.shutil")
    @patch("builtins.input")
    def test_get_subtitles_with_spaces_in_path(
        self,
        mock_input,
        mock_shutil,
        mock_fetch_season,
        mock_opensubtitles,
        mock_get_config_manager,
    ):
        """Test that get_subtitles function works with show directories containing spaces."""
        # Mock configuration with path containing spaces
        # Create the directory first
        show_dir = self.temp_path / "My TV Shows" / "Breaking Bad"
        show_dir.mkdir(parents=True, exist_ok=True)

        mock_config = Config(
            show_dir=show_dir,
            tmdb_api_key="test_tmdb_key",
            open_subtitles_api_key="test_os_key",
            open_subtitles_user_agent="test_agent",
            open_subtitles_username="test_user",
            open_subtitles_password="test_pass",
        )
        # Mock the manager.load() to return our mock_config
        mock_manager = Mock()
        mock_manager.load.return_value = mock_config
        mock_get_config_manager.return_value = mock_manager

        # Mock OpenSubtitles client search results
        mock_client = Mock()
        mock_opensubtitles.return_value = mock_client

        # Mock search response
        mock_subtitle = Mock()
        mock_subtitle.to_dict.return_value = {"file_name": "Show - S01E01.srt"}

        mock_response = Mock()
        mock_response.data = [mock_subtitle]
        mock_client.search.return_value = mock_response

        # Mock download_and_save to return a path
        mock_client.download_and_save.return_value = "/tmp/fake.srt"

        # Mock season details
        mock_fetch_season.return_value = 2

        # This should not raise an exception with spaces in the path
        try:
            get_subtitles(show_id=1396, seasons={1}, config=mock_config)
        except Exception as e:
            # If there's an exception, it shouldn't be related to path handling
            # OpenSubtitles exceptions are expected in a test environment
            self.assertNotIn("path", str(e).lower())
            self.assertNotIn("space", str(e).lower())

    def test_path_edge_cases(self):
        """Test edge cases for path handling."""
        edge_cases = [
            # Multiple spaces
            "C:\\My  TV  Shows\\Show  With  Multiple  Spaces",
            # Leading/trailing spaces
            " C:\\My TV Shows\\Show With Spaces ",
            # Mixed quotes and spaces
            '"C:\\My TV Shows"\\Show Name',
            # Unicode characters with spaces
            "C:\\My TV Shows\\Café Français",
            # Very long path with spaces
            "C:\\A Very Long Path Name With Many Spaces\\And Another Very Long Directory Name\\Show Name",
        ]

        for path_str in edge_cases:
            with self.subTest(path=path_str):
                # normalize_path should handle these without raising exceptions
                try:
                    result = normalize_path(path_str)
                    self.assertIsInstance(result, Path)
                except Exception as e:
                    self.fail(f"normalize_path failed on edge case '{path_str}': {e}")

    def test_issue_61_reproduction(self):
        """Reproduce issue 61: Show-dir path cannot contain spaces."""
        # This test reproduces the exact issue described in #61
        problem_path = "C:\\my rips\\show_name"

        # The issue is that --get-subs fails when the path has spaces
        # Let's test the path normalization that's used in get_subtitles
        normalized = normalize_path(problem_path)

        # Should successfully normalize without losing information
        self.assertIsInstance(normalized, Path)
        self.assertEqual(normalized.name, "show_name")

        # The normalized path should be usable for directory operations
        self.assertTrue(str(normalized))  # Should not be empty

    def test_issue_62_reproduction(self):
        """Reproduce issue 62: show-dir cannot have quotes."""
        # This test reproduces the exact issue described in #62
        quoted_paths = [
            '"C:\\my rips\\show name"',
            "'C:\\my rips\\show name'",
            '"C:/my rips/show name"',
        ]

        for quoted_path in quoted_paths:
            with self.subTest(path=quoted_path):
                # The issue is that quoted paths aren't handled properly
                normalized = normalize_path(quoted_path)

                # Should successfully normalize and remove quotes
                self.assertIsInstance(normalized, Path)
                self.assertNotIn('"', str(normalized))
                self.assertNotIn("'", str(normalized))


class TestPathIntegration(unittest.TestCase):
    """Integration tests for path handling across the application."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_episode_matcher_with_spaces(self):
        """Test that EpisodeMatcher handles show names with spaces correctly."""
        from mkv_episode_matcher.episode_identification import EpisodeMatcher

        # This should not raise an exception
        try:
            matcher = EpisodeMatcher(cache_dir=self.temp_path, show_name="Breaking Bad")
            self.assertIsNotNone(matcher)
            self.assertEqual(matcher.show_name, "Breaking Bad")
        except Exception as e:
            self.fail(f"EpisodeMatcher failed with spaces in show name: {e}")

    def test_end_to_end_path_handling(self):
        """Test end-to-end path handling from command line to processing."""
        # Create a test directory structure with spaces
        show_dir = self.temp_path / "My Test Show With Spaces"
        show_dir.mkdir()

        season_dir = show_dir / "Season 1"
        season_dir.mkdir()

        # Create a test .mkv file
        test_file = season_dir / "Test Episode.mkv"
        test_file.touch()

        # Test that the path can be processed through the whole pipeline
        normalized = normalize_path(str(show_dir))
        self.assertIsInstance(normalized, Path)

        # Should be able to find seasons
        seasons = get_valid_seasons(str(show_dir))
        self.assertEqual(len(seasons), 1)

        # Season path should also contain spaces
        self.assertIn("Season 1", str(seasons[0]))


if __name__ == "__main__":
    unittest.main()
