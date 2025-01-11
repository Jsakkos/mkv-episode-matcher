import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from mkv_episode_matcher.episode_matcher import process_show
from mkv_episode_matcher.utils import (
    get_valid_seasons,
    check_filename,
    rename_episode_file,
    clean_text,
    extract_season_episode
)
from mkv_episode_matcher.episode_identification import EpisodeMatcher
from mkv_episode_matcher.config import get_config, set_config
from unittest.mock import Mock, patch


# @pytest.fixture
# def mock_config():
#     return {
#         "tmdb_api_key": "test_key",
#         "show_dir": "/test/path",
#         "max_threads": 4,
#         "tesseract_path": "/usr/bin/tesseract",
#     }


@pytest.fixture
def mock_episode_data():
    return {
        "name": "Test Episode",
        "season_number": 1,
        "episode_number": 1,
        "overview": "Test overview",
    }

@pytest.fixture
def mock_seasons():
    return ["/test/path/Season 1"]

@pytest.fixture
def temp_show_dir(tmp_path):
    show_dir = tmp_path / "Test Show"
    show_dir.mkdir()
    season_dir = show_dir / "Season 1"
    season_dir.mkdir()
    (season_dir / "episode1.mkv").touch()
    (season_dir / "episode2.mkv").touch()
    return show_dir

@pytest.fixture
def mock_config():
    return {
        "tmdb_api_key": "test_key",
        "show_dir": "/test/path",
        "max_threads": 4,
        "open_subtitles_api_key": "test_key",
        "open_subtitles_user_agent": "test_agent",
        "open_subtitles_username": "test_user",
        "open_subtitles_password": "test_pass",
        "tesseract_path": "/test/tesseract"
    }

class TestUtilities:
    def test_get_valid_seasons(self, temp_show_dir):
        seasons = get_valid_seasons(str(temp_show_dir))
        assert len(seasons) == 1
        assert str(temp_show_dir / "Season 1") in seasons

    def test_check_filename(self):
        assert check_filename("Show - S01E02.mkv") == True
        assert check_filename("random_file.mkv") == False

    def test_rename_episode_file(self, temp_show_dir):
        original = temp_show_dir / "Season 1" / "episode1.mkv"
        new_name = "Show - S01E01.mkv"
        result = rename_episode_file(str(original), new_name)
        assert result is not None
        assert Path(result).name == new_name

    def test_clean_text(self):
        text = "Test [action] (note) {tag}"
        assert clean_text(text) == "Test"

    def test_extract_season_episode(self):
        filename = "Show - S01E02.mkv"
        season, episode = extract_season_episode(filename)
        assert season == 1
        assert episode == 2

class TestConfiguration:
    def test_set_config(self, tmp_path, mock_config):
        config_file = tmp_path / "config.ini"
        set_config(
            mock_config["tmdb_api_key"],
            mock_config["open_subtitles_api_key"],
            mock_config["open_subtitles_user_agent"],
            mock_config["open_subtitles_username"],
            mock_config["open_subtitles_password"],
            mock_config["show_dir"],
            str(config_file),
            mock_config["tesseract_path"]
        )
        assert config_file.exists()

    def test_get_config(self, tmp_path, mock_config):
        config_file = tmp_path / "config.ini"
        set_config(
            mock_config["tmdb_api_key"],
            mock_config["open_subtitles_api_key"],
            mock_config["open_subtitles_user_agent"],
            mock_config["open_subtitles_username"],
            mock_config["open_subtitles_password"],
            mock_config["show_dir"],
            str(config_file),
            mock_config["tesseract_path"]
        )
        config = get_config(str(config_file))
        assert config["tmdb_api_key"] == mock_config["tmdb_api_key"]
        assert config["show_dir"] == mock_config["show_dir"]

class TestEpisodeMatcher:
    @pytest.fixture
    def matcher(self, tmp_path):
        return EpisodeMatcher(tmp_path, "Test Show")

    def test_clean_text(self, matcher):
        text = "Test [action] T-t-test"
        assert matcher.clean_text(text) == "test action test"

    def test_chunk_score(self, matcher):
        score = matcher.chunk_score("Test dialogue", "test dialog")
        assert 0 <= score <= 1

    @patch('subprocess.run')
    def test_extract_audio_chunk(self, mock_run, matcher, tmp_path):
        mkv_file = tmp_path / "test.mkv"
        mkv_file.touch()
        chunk = matcher.extract_audio_chunk(str(mkv_file), 0)
        assert isinstance(chunk, str)
        assert mock_run.called

class TestEpisodeMatcher:
    def test_extract_season_episode(self):
        from mkv_episode_matcher.utils import extract_season_episode

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


if __name__ == '__main__':
    pytest.main(['-v'])