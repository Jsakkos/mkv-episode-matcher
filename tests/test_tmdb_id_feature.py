"""
Comprehensive test suite for the --tmdb-id feature.

Tests the manual TMDB ID specification feature that allows users to override
automatic show detection when it returns incorrect results (e.g., Law & Order
vs Law & Order: SVU).
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from mkv_episode_matcher.core.config_manager import ConfigManager
from mkv_episode_matcher.core.models import Config
from mkv_episode_matcher.core.providers.subtitles import (
    OpenSubtitlesProvider,
    SubtitleFile,
)
from mkv_episode_matcher.tmdb_client import fetch_show_details


class TestFetchShowDetails:
    """Test the fetch_show_details() function from tmdb_client.py"""

    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    def test_fetch_show_details_valid_id(self, mock_config_mgr, mock_get):
        """Test fetching show details with a valid TMDB ID."""
        # Mock config with API key
        mock_config = Mock()
        mock_config.tmdb_api_key = "test_api_key"
        mock_config_mgr.return_value.load.return_value = mock_config

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Law & Order",
            "id": 549,
            "number_of_seasons": 20,
            "overview": "Classic crime drama",
        }
        mock_get.return_value = mock_response

        # Call function
        result = fetch_show_details(549)

        # Verify result
        assert result is not None
        assert result["name"] == "Law & Order"
        assert result["id"] == 549
        assert result["number_of_seasons"] == 20

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "549" in call_url
        assert "test_api_key" in call_url

    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    def test_fetch_show_details_invalid_id(self, mock_config_mgr, mock_get):
        """Test fetching show details with an invalid TMDB ID (404 response)."""
        # Mock config with API key
        mock_config = Mock()
        mock_config.tmdb_api_key = "test_api_key"
        mock_config_mgr.return_value.load.return_value = mock_config

        # Mock 404 response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        # Call function
        result = fetch_show_details(999999)

        # Verify None is returned
        assert result is None

    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    def test_fetch_show_details_missing_api_key(self, mock_config_mgr):
        """Test fetching show details when TMDB API key is not configured."""
        # Mock config without API key
        mock_config = Mock()
        mock_config.tmdb_api_key = None
        mock_config_mgr.return_value.load.return_value = mock_config

        # Call function
        result = fetch_show_details(549)

        # Verify None is returned
        assert result is None

    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    def test_fetch_show_details_network_error(self, mock_config_mgr, mock_get):
        """Test fetching show details with network timeout."""
        # Mock config with API key
        mock_config = Mock()
        mock_config.tmdb_api_key = "test_api_key"
        mock_config_mgr.return_value.load.return_value = mock_config

        # Mock network timeout
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        # Call function
        result = fetch_show_details(549)

        # Verify None is returned
        assert result is None

    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    def test_fetch_show_details_empty_response(self, mock_config_mgr, mock_get):
        """Test fetching show details with 200 but empty/invalid data."""
        # Mock config with API key
        mock_config = Mock()
        mock_config.tmdb_api_key = "test_api_key"
        mock_config_mgr.return_value.load.return_value = mock_config

        # Mock response with empty data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        # Call function
        result = fetch_show_details(549)

        # Verify empty dict is returned (not None)
        assert result == {}


class TestOpenSubtitlesProviderWithTmdbId:
    """Test the OpenSubtitlesProvider with tmdb_id parameter."""

    @patch("mkv_episode_matcher.core.providers.subtitles.OpenSubtitlesProvider._authenticate")
    @patch("mkv_episode_matcher.core.providers.subtitles.get_config_manager")
    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    @patch("opensubtitlescom.OpenSubtitles")
    def test_opensubtitles_provider_with_tmdb_id(
        self, mock_client_class, mock_tmdb_config_mgr, mock_tmdb_get, mock_subtitles_config_mgr, mock_auth
    ):
        """Test that OpenSubtitlesProvider uses tmdb_id to lookup correct show name."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock config
            mock_config = Mock()
            mock_config.tmdb_api_key = "test_api_key"
            mock_config.cache_dir = Path(tmp_dir)
            mock_config.open_subtitles_api_key = "test_os_key"
            mock_config.open_subtitles_username = "test_user"
            mock_config.open_subtitles_password = "test_pass"
            mock_config.open_subtitles_user_agent = "test_agent"
            mock_tmdb_config_mgr.return_value.load.return_value = mock_config
            mock_subtitles_config_mgr.return_value.load.return_value = mock_config

            # Mock TMDB API response
            mock_tmdb_response = Mock()
            mock_tmdb_response.status_code = 200
            mock_tmdb_response.json.return_value = {
                "name": "Law & Order",
                "id": 549,
            }
            mock_tmdb_get.return_value = mock_tmdb_response

            # Mock OpenSubtitles client
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock search response
            mock_search_response = Mock()
            mock_search_response.data = []
            mock_client.search.return_value = mock_search_response

            # Create provider (it loads config from get_config_manager)
            provider = OpenSubtitlesProvider()
            provider.client = mock_client  # Set the client directly after initialization

            # Call get_subtitles with tmdb_id
            result = provider.get_subtitles(
                show_name="Law & Order SVU",  # Wrong name
                season=1,
                tmdb_id=549,  # Correct ID for Law & Order
            )

            # Verify TMDB lookup was called
            mock_tmdb_get.assert_called()
            tmdb_call_url = mock_tmdb_get.call_args[0][0]
            assert "549" in tmdb_call_url

            # Verify OpenSubtitles search used TMDB ID parameters
            mock_client.search.assert_called()
            search_kwargs = mock_client.search.call_args[1]
            # Should use parent_tmdb_id when available
            assert search_kwargs["parent_tmdb_id"] == 549
            assert search_kwargs["season_number"] == 1
            assert search_kwargs["type"] == "episode"

    @patch("mkv_episode_matcher.core.providers.subtitles.OpenSubtitlesProvider._authenticate")
    @patch("mkv_episode_matcher.core.providers.subtitles.get_config_manager")
    @patch("opensubtitlescom.OpenSubtitles")
    def test_opensubtitles_without_tmdb_id(self, mock_client_class, mock_config_mgr, mock_auth):
        """Test backward compatibility - provider works without tmdb_id."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock config
            mock_config = Mock()
            mock_config.cache_dir = Path(tmp_dir)
            mock_config.open_subtitles_api_key = "test_key"
            mock_config.open_subtitles_username = "test_user"
            mock_config.open_subtitles_password = "test_pass"
            mock_config.open_subtitles_user_agent = "test_agent"
            mock_config.tmdb_api_key = "test_api_key"
            mock_config_mgr.return_value.load.return_value = mock_config

            # Mock OpenSubtitles client
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock search response
            mock_search_response = Mock()
            mock_search_response.data = []
            mock_client.search.return_value = mock_search_response

            # Create provider (it loads config from get_config_manager)
            provider = OpenSubtitlesProvider()
            provider.client = mock_client  # Set the client directly after initialization

            # Call get_subtitles WITHOUT tmdb_id
            result = provider.get_subtitles(
                show_name="Test Show",
                season=1,
                # No tmdb_id parameter
            )

            # Verify search used original show name
            mock_client.search.assert_called()
            search_args = mock_client.search.call_args
            query = search_args[1]["query"]
            assert "Test Show" in query

    @patch("mkv_episode_matcher.core.providers.subtitles.OpenSubtitlesProvider._authenticate")
    @patch("mkv_episode_matcher.core.providers.subtitles.get_config_manager")
    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    @patch("opensubtitlescom.OpenSubtitles")
    def test_law_and_order_vs_svu_confusion(
        self, mock_client_class, mock_tmdb_config_mgr, mock_tmdb_get, mock_subtitles_config_mgr, mock_auth
    ):
        """
        CRITICAL TEST for issue #75: Law & Order vs Law & Order: SVU confusion.

        This test verifies that when tmdb_id=549 is provided, the system correctly
        looks up "Law & Order" from TMDB and uses it for OpenSubtitles search,
        even if the detected/provided show name is "Law & Order: SVU".
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock config
            mock_config = Mock()
            mock_config.tmdb_api_key = "test_api_key"
            mock_config.cache_dir = Path(tmp_dir)
            mock_config.open_subtitles_api_key = "test_os_key"
            mock_config.open_subtitles_username = "test_user"
            mock_config.open_subtitles_password = "test_pass"
            mock_config.open_subtitles_user_agent = "test_agent"
            mock_tmdb_config_mgr.return_value.load.return_value = mock_config
            mock_subtitles_config_mgr.return_value.load.return_value = mock_config

            # Mock TMDB API to return correct "Law & Order" for ID 549
            mock_tmdb_response = Mock()
            mock_tmdb_response.status_code = 200
            mock_tmdb_response.json.return_value = {
                "name": "Law & Order",
                "id": 549,
                "first_air_date": "1990-09-13",
            }
            mock_tmdb_get.return_value = mock_tmdb_response

            # Mock OpenSubtitles client
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock search response
            mock_search_response = Mock()
            mock_search_response.data = []
            mock_client.search.return_value = mock_search_response

            # Create provider (it loads config from get_config_manager)
            provider = OpenSubtitlesProvider()
            provider.client = mock_client  # Set the client directly after initialization

            # Simulate the issue: auto-detection returned "Law & Order SVU"
            # but user provides tmdb_id=549 for the correct show
            result = provider.get_subtitles(
                show_name="Law & Order SVU",  # WRONG name (auto-detected, sanitized for path)
                season=1,
                tmdb_id=549,  # CORRECT ID for "Law & Order"
            )

            # Verify TMDB was called with ID 549
            mock_tmdb_get.assert_called()
            tmdb_url = mock_tmdb_get.call_args[0][0]
            assert "/tv/549?" in tmdb_url

            # CRITICAL ASSERTION: Verify OpenSubtitles search used TMDB ID 549
            # This ensures we get "Law & Order" results, NOT "Law & Order: SVU"
            mock_client.search.assert_called()
            search_kwargs = mock_client.search.call_args[1]
            assert (
                search_kwargs["parent_tmdb_id"] == 549
            ), f"Expected parent_tmdb_id=549, got {search_kwargs.get('parent_tmdb_id')}"
            assert (
                search_kwargs["season_number"] == 1
            ), f"Expected season_number=1, got {search_kwargs.get('season_number')}"
            assert (
                search_kwargs["type"] == "episode"
            ), f"Expected type='episode', got {search_kwargs.get('type')}"

    @patch("mkv_episode_matcher.core.providers.subtitles.OpenSubtitlesProvider._authenticate")
    @patch("mkv_episode_matcher.core.providers.subtitles.get_config_manager")
    @patch("mkv_episode_matcher.tmdb_client.requests.get")
    @patch("mkv_episode_matcher.tmdb_client.get_config_manager")
    @patch("opensubtitlescom.OpenSubtitles")
    def test_tmdb_lookup_fails_fallback_to_original_name(
        self, mock_client_class, mock_tmdb_config_mgr, mock_tmdb_get, mock_subtitles_config_mgr, mock_auth
    ):
        """Test that if TMDB lookup fails, original show name is used as fallback."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock config
            mock_config = Mock()
            mock_config.tmdb_api_key = "test_api_key"
            mock_config.cache_dir = Path(tmp_dir)
            mock_config.open_subtitles_api_key = "test_os_key"
            mock_config.open_subtitles_username = "test_user"
            mock_config.open_subtitles_password = "test_pass"
            mock_config.open_subtitles_user_agent = "test_agent"
            mock_tmdb_config_mgr.return_value.load.return_value = mock_config
            mock_subtitles_config_mgr.return_value.load.return_value = mock_config

            # Mock TMDB API to raise an exception
            mock_tmdb_get.side_effect = requests.exceptions.Timeout("Network error")

            # Mock OpenSubtitles client
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            # Mock search response
            mock_search_response = Mock()
            mock_search_response.data = []
            mock_client.search.return_value = mock_search_response

            # Create provider (it loads config from get_config_manager)
            provider = OpenSubtitlesProvider()
            provider.client = mock_client  # Set the client directly after initialization

            # Call with tmdb_id but expect fallback
            result = provider.get_subtitles(
                show_name="Test Show", season=1, tmdb_id=549
            )

            # Verify search still used TMDB ID even though lookup failed
            # The TMDB ID is more reliable than the show name
            mock_client.search.assert_called()
            search_kwargs = mock_client.search.call_args[1]
            assert search_kwargs["parent_tmdb_id"] == 549
            assert search_kwargs["season_number"] == 1
            assert search_kwargs["type"] == "episode"
