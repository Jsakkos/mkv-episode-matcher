from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_config():
    return {
        "tmdb_api_key": "test_key",
        "show_dir": "/test/path",
        "max_threads": 4,
        "tesseract_path": "/usr/bin/tesseract",
    }


@pytest.fixture
def mock_episode_data():
    return {
        "name": "Test Episode",
        "season_number": 1,
        "episode_number": 1,
        "overview": "Test overview",
    }


class TestEpisodeMatcher:
    def test_extract_season_episode(self):
        from mkv_episode_matcher.episode_matcher import extract_season_episode

        # Test valid filename
        assert extract_season_episode("Show - S01E02.mkv") == (1, 2)

        # Test invalid filename
        assert extract_season_episode("invalid.mkv") == (None, None)

    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    def test_fetch_show_id(self, mock_get):
        from mkv_episode_matcher.tmdb_client import fetch_show_id

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"id": 12345}]}
        mock_get.return_value = mock_response

        assert fetch_show_id("Test Show") == "12345"

    @patch("mkv_episode_matcher.utils.OpenSubtitles")
    def test_get_subtitles(self, mock_subtitles):
        from mkv_episode_matcher.utils import get_subtitles

        # Test subtitle download
        mock_subtitles.return_value.search.return_value.data = [
            {"file_name": "Test.Show.S01E01.srt"}
        ]

        with patch("pathlib.Path.exists", return_value=False):
            get_subtitles(12345, {1})

            mock_subtitles.return_value.download_and_save.assert_called_once()
