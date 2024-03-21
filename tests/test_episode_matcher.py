import unittest
from unittest.mock import MagicMock, patch
import os
from unittest.mock import MagicMock, patch
import os

from episode_matcher import process_show
from episode_matcher import process_season

class TestProcessSeason(unittest.TestCase):
    @patch('episode_matcher.get_config')
    @patch('episode_matcher.logger')
    @patch('episode_matcher.check_filename')
    @patch('episode_matcher.find_matching_episode')
    @patch('episode_matcher.rename_episode_file')
    def test_process_season_with_matching_episodes(self, mock_rename, mock_find, mock_check, mock_logger, mock_get_config):
        # Mock the necessary dependencies
        mock_get_config.return_value = {"show_dir": "/path/to/show"}
        mock_check.return_value = False
        mock_find.return_value = "S01E01"

        # Set up the test data
        show_id = "12345"
        season_number = 1
        season_path = "/path/to/season"
        season_hashes = {"episode1.mkv": "hash1", "episode2.mkv": "hash2"}
        force = False
        dry_run = False
        threshold = None

        # Call the function
        process_season(show_id, season_number, season_path, season_hashes, force, dry_run, threshold)

        # Assert that the necessary functions were called with the correct arguments
        mock_logger.info.assert_called_with("Processing Season 1...")
        mock_get_config.assert_called_with("/d:/mkv-episode-matcher/mkv_episode_matcher/config.json")
        mock_check.assert_called_with("episode1.mkv", "show", 1, 0)
        mock_find.assert_called_with("/path/to/season/episode1.mkv", "/path/to/season", 1, season_hashes, matching_threshold=None)
        mock_rename.assert_called_with("/path/to/season/episode1.mkv", 1, "S01E01")

    @patch('episode_matcher.get_config')
    @patch('episode_matcher.logger')
    @patch('episode_matcher.check_filename')
    @patch('episode_matcher.find_matching_episode')
    @patch('episode_matcher.rename_episode_file')
    def test_process_season_with_no_matching_episodes(self, mock_rename, mock_find, mock_check, mock_logger, mock_get_config):
        # Mock the necessary dependencies
        mock_get_config.return_value = {"show_dir": "/path/to/show"}
        mock_check.return_value = False
        mock_find.return_value = None

        # Set up the test data
        show_id = "12345"
        season_number = 1
        season_path = "/path/to/season"
        season_hashes = {"episode1.mkv": "hash1", "episode2.mkv": "hash2"}
        force = False
        dry_run = False
        threshold = None

        # Call the function
        process_season(show_id, season_number, season_path, season_hashes, force, dry_run, threshold)

        # Assert that the necessary functions were called with the correct arguments
        mock_logger.info.assert_called_with("Processing Season 1...")
        mock_get_config.assert_called_with("/d:/mkv-episode-matcher/mkv_episode_matcher/config.json")
        mock_check.assert_called_with("episode1.mkv", "show", 1, 0)
        mock_find.assert_called_with("/path/to/season/episode1.mkv", "/path/to/season", 1, season_hashes, matching_threshold=None)
        mock_rename.assert_not_called()


class TestProcessShow(unittest.TestCase):
    @patch('episode_matcher.get_config')
    @patch('episode_matcher.fetch_show_id')
    @patch('episode_matcher.preprocess_hashes')
    @patch('episode_matcher.process_season')
    def test_process_show_with_season(self, mock_process_season, mock_preprocess_hashes, mock_fetch_show_id, mock_get_config):
        # Mock the necessary dependencies
        mock_get_config.return_value = {"api_key": "12345", "show_dir": "/path/to/show"}
        mock_fetch_show_id.return_value = "67890"
        mock_preprocess_hashes.return_value = {"1": {"episode1.mkv": "hash1", "episode2.mkv": "hash2"}}

        # Set up the test data
        season = 1
        force = False
        dry_run = False
        threshold = None

        # Call the function
        process_show(season, force, dry_run, threshold)

        # Assert that the necessary functions were called with the correct arguments
        mock_get_config.assert_called_with("/d:/mkv-episode-matcher/mkv_episode_matcher/config.json")
        mock_fetch_show_id.assert_called_with("show")
        mock_preprocess_hashes.assert_called_with("show", "67890", [1])
        mock_process_season.assert_called_with("67890", 1, "/path/to/show/Season 1", {"episode1.mkv": "hash1", "episode2.mkv": "hash2"}, force, dry_run, threshold)

    @patch('episode_matcher.get_config')
    @patch('episode_matcher.fetch_show_id')
    @patch('episode_matcher.preprocess_hashes')
    @patch('episode_matcher.process_season')
    def test_process_show_without_season(self, mock_process_season, mock_preprocess_hashes, mock_fetch_show_id, mock_get_config):
        # Mock the necessary dependencies
        mock_get_config.return_value = {"api_key": "12345", "show_dir": "/path/to/show"}
        mock_fetch_show_id.return_value = "67890"
        mock_preprocess_hashes.return_value = {"1": {"episode1.mkv": "hash1", "episode2.mkv": "hash2"}, "2": {"episode3.mkv": "hash3"}}

        # Set up the test data
        season = None
        force = False
        dry_run = False
        threshold = None

        # Call the function
        process_show(season, force, dry_run, threshold)

        # Assert that the necessary functions were called with the correct arguments
        mock_get_config.assert_called_with("/d:/mkv-episode-matcher/mkv_episode_matcher/config.json")
        mock_fetch_show_id.assert_called_with("show")
        mock_preprocess_hashes.assert_called_with("show", "67890", [1, 2])
        mock_process_season.assert_any_call("67890", 1, "/path/to/show/Season 1", {"episode1.mkv": "hash1", "episode2.mkv": "hash2"}, force, dry_run, threshold)
        mock_process_season.assert_any_call("67890", 2, "/path/to/show/Season 2", {"episode3.mkv": "hash3"}, force, dry_run, threshold)


if __name__ == '__main__':
    unittest.main()