"""Test cases for config.py handling of special characters in passwords."""

import tempfile
from pathlib import Path

import pytest

from mkv_episode_matcher.config import get_config, set_config


class TestConfigSpecialCharacters:
    """Test that config handling works correctly with special characters in passwords."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def mock_config_data(self):
        """Mock configuration data for testing."""
        return {
            "tmdb_api_key": "test_tmdb_api_key",
            "open_subtitles_api_key": "test_os_api_key",
            "open_subtitles_user_agent": "test_user_agent",
            "open_subtitles_username": "test_username",
            "show_dir": "/test/path"
        }

    def test_password_with_percent_symbol(self, temp_config_file, mock_config_data):
        """Test that passwords containing % symbol don't cause interpolation errors."""
        password_with_percent = "H7z*X$X29JdJ^#%Q"  # gitguardian:ignore
        
        # This should not raise a ValueError
        set_config(
            mock_config_data["tmdb_api_key"],
            mock_config_data["open_subtitles_api_key"],
            mock_config_data["open_subtitles_user_agent"],
            mock_config_data["open_subtitles_username"],
            password_with_percent,
            mock_config_data["show_dir"],
            temp_config_file,
        )
        
        # Verify the config was written successfully
        config = get_config(temp_config_file)
        assert config is not None
        assert config["open_subtitles_password"] == password_with_percent

    def test_password_with_multiple_percent_symbols(self, temp_config_file, mock_config_data):
        """Test that passwords with multiple % symbols work correctly."""
        password_with_percents = "password%with%multiple%percent%signs"
        
        set_config(
            mock_config_data["tmdb_api_key"],
            mock_config_data["open_subtitles_api_key"],
            mock_config_data["open_subtitles_user_agent"],
            mock_config_data["open_subtitles_username"],
            password_with_percents,
            mock_config_data["show_dir"],
            temp_config_file,
        )
        
        config = get_config(temp_config_file)
        assert config["open_subtitles_password"] == password_with_percents

    def test_password_with_interpolation_like_syntax(self, temp_config_file, mock_config_data):
        """Test that passwords resembling interpolation syntax are handled correctly."""
        # This resembles ConfigParser interpolation syntax but should be treated literally
        password_with_interpolation = "%(section)s_password_%(option)s"
        
        set_config(
            mock_config_data["tmdb_api_key"],
            mock_config_data["open_subtitles_api_key"],
            mock_config_data["open_subtitles_user_agent"],
            mock_config_data["open_subtitles_username"],
            password_with_interpolation,
            mock_config_data["show_dir"],
            temp_config_file,
        )
        
        config = get_config(temp_config_file)
        assert config["open_subtitles_password"] == password_with_interpolation

    def test_password_with_various_special_characters(self, temp_config_file, mock_config_data):
        """Test that passwords with various special characters work correctly."""
        special_passwords = [
            "pass@word!123",
            "my$ecret#key*",
            "complex&password^with()brackets[]",
            "unicode_测试_password",
            "spaces in password",
            "tabs\tand\nnewlines",
        ]
        
        for password in special_passwords:
            set_config(
                mock_config_data["tmdb_api_key"],
                mock_config_data["open_subtitles_api_key"],
                mock_config_data["open_subtitles_user_agent"],
                mock_config_data["open_subtitles_username"],
                password,
                mock_config_data["show_dir"],
                temp_config_file,
            )
            
            config = get_config(temp_config_file)
            assert config["open_subtitles_password"] == password, f"Failed for password: {password}"

    def test_original_bug_case(self, temp_config_file, mock_config_data):
        """Test the specific password from the original bug report."""
        # This is the exact password that caused the original issue
        problematic_password = "H7z*X$X29JdJ^#%Q"  # gitguardian:ignore
        
        # Before the fix, this would raise:
        # ValueError: invalid interpolation syntax in 'H7z*X$X29JdJ^#%Q' at position 14
        set_config(
            mock_config_data["tmdb_api_key"],
            mock_config_data["open_subtitles_api_key"],
            mock_config_data["open_subtitles_user_agent"],
            mock_config_data["open_subtitles_username"],
            problematic_password,
            mock_config_data["show_dir"],
            temp_config_file,
        )
        
        # Verify we can read it back correctly
        config = get_config(temp_config_file)
        assert config is not None
        assert config["open_subtitles_password"] == problematic_password
        
        # Verify all other fields are preserved
        assert config["tmdb_api_key"] == mock_config_data["tmdb_api_key"]
        assert config["open_subtitles_username"] == mock_config_data["open_subtitles_username"]
        assert config["show_dir"] == mock_config_data["show_dir"]

    def test_empty_password(self, temp_config_file, mock_config_data):
        """Test that empty passwords are handled correctly."""
        empty_password = ""
        
        set_config(
            mock_config_data["tmdb_api_key"],
            mock_config_data["open_subtitles_api_key"],
            mock_config_data["open_subtitles_user_agent"],
            mock_config_data["open_subtitles_username"],
            empty_password,
            mock_config_data["show_dir"],
            temp_config_file,
        )
        
        config = get_config(temp_config_file)
        assert config["open_subtitles_password"] == empty_password

    def test_config_persistence(self, temp_config_file, mock_config_data):
        """Test that config values persist correctly across multiple operations."""
        password = "persistent%password#123"
        
        # Set config
        set_config(
            mock_config_data["tmdb_api_key"],
            mock_config_data["open_subtitles_api_key"],
            mock_config_data["open_subtitles_user_agent"],
            mock_config_data["open_subtitles_username"],
            password,
            mock_config_data["show_dir"],
            temp_config_file,
        )
        
        # Read config multiple times to ensure consistency
        for _ in range(3):
            config = get_config(temp_config_file)
            assert config["open_subtitles_password"] == password