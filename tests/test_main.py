from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mkv_episode_matcher.core.models import Config
from mkv_episode_matcher.utils import (
    check_filename,
    clean_text,
    extract_season_episode,
    get_valid_seasons,
    rename_episode_file,
)


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
def mock_config(tmp_path):
    show_dir = tmp_path / "test_show_dir"
    show_dir.mkdir()
    return {
        "tmdb_api_key": "test_key",
        "show_dir": str(show_dir),
        "open_subtitles_api_key": "test_key",
        "open_subtitles_user_agent": "test_agent",
        "open_subtitles_username": "test_user",
        "open_subtitles_password": "test_pass",
    }


class TestUtilities:
    def test_get_valid_seasons(self, temp_show_dir):
        seasons = get_valid_seasons(str(temp_show_dir))
        assert len(seasons) == 1
        assert str(temp_show_dir / "Season 1") in seasons

    def test_check_filename(self):
        assert check_filename("Show - S01E02.mkv") is True
        assert check_filename("random_file.mkv") is False

    def test_rename_episode_file(self, temp_show_dir):
        original = temp_show_dir / "Season 1" / "episode1.mkv"
        new_name = "Show - S01E01.mkv"
        result = rename_episode_file(str(original), new_name)
        assert result is not None
        assert Path(result).name == new_name

    def test_clean_text(self):
        text = "Test [action] (note) {tag}"
        assert clean_text(text) == "Test"

        # Test that years are preserved
        text_with_year = "Bluey (2018)"
        assert clean_text(text_with_year) == "Bluey (2018)"

        # Test mixed content with year
        text_mixed = "Show Name [HD] (2020) {release}"
        assert clean_text(text_mixed) == "Show Name (2020)"

    def test_clean_text_edge_cases(self):
        """Test edge cases for clean_text function reported by users."""
        # Test exact user reported case
        bluey_case = "Bluey (2018)"
        assert clean_text(bluey_case) == "Bluey (2018)"

        # Test with extra whitespace and tags
        bluey_with_junk = "Bluey [1080p] (2018) {AMZN}"
        assert clean_text(bluey_with_junk) == "Bluey (2018)"

        # Test show name with multiple years (should preserve all)
        multiple_years = "Show (1999) vs Show (2020)"
        assert clean_text(multiple_years) == "Show (1999) vs Show (2020)"

        # Test year at beginning
        year_first = "(2018) Bluey [HD]"
        assert clean_text(year_first) == "(2018) Bluey"

        # Test year with other content in same parentheses (should remove)
        year_with_text = "Show (2018 Remaster)"
        assert clean_text(year_with_text) == "Show"

        # Test 4-digit numbers (preserves any 4-digit number in parentheses)
        four_digit = "Show (1234)"
        assert clean_text(four_digit) == "Show (1234)"

        # Test edge case years
        assert clean_text("Show (1900)") == "Show (1900)"  # Very old year
        assert clean_text("Show (2099)") == "Show (2099)"  # Future year

        # Test multiple spaces and normalization
        messy_spacing = "Bluey    [HD]     (2018)    {RELEASE}"
        assert clean_text(messy_spacing) == "Bluey (2018)"

    def test_extract_season_episode(self):
        filename = "Show - S01E02.mkv"
        season, episode = extract_season_episode(filename)
        assert season == 1
        assert episode == 2


class TestConfiguration:
    def test_save_config(self, tmp_path, mock_config):
        config_file = tmp_path / "config.json"

        # Create ConfigManager with temp file
        from mkv_episode_matcher.core.config_manager import ConfigManager

        cm = ConfigManager(config_path=config_file)

        # Create config object
        config = Config(**mock_config)
        # Note: Config model names might differ slightly from mock_config keys if aliases are used,
        # but let's assume they match for now based on previous usage or I'll map them.
        # Check Config model fields: tmdb_api_key, show_dir, etc.
        # Subtitle args are: open_subtitles_*

        cm.save(config)
        assert config_file.exists()

    def test_load_config(self, tmp_path, mock_config):
        config_file = tmp_path / "config.json"

        from mkv_episode_matcher.core.config_manager import ConfigManager

        cm = ConfigManager(config_path=config_file)

        config = Config(**mock_config)
        cm.save(config)

        loaded_config = cm.load()
        assert loaded_config.tmdb_api_key == mock_config["tmdb_api_key"]
        assert str(loaded_config.show_dir) == str(Path(mock_config["show_dir"]))


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


if __name__ == "__main__":
    pytest.main(["-v"])
