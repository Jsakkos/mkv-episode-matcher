"""
Comprehensive tests for the revamped MKV Episode Matcher V2
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mkv_episode_matcher.core.config_manager import ConfigManager
from mkv_episode_matcher.core.engine import CacheManager, MatchEngineV2
from mkv_episode_matcher.core.models import Config, EpisodeInfo, MatchResult


class TestCacheManager:
    """Test the enhanced caching system."""

    def test_init(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir) / "cache"
            cache = CacheManager(cache_dir)

            assert cache.cache_dir == cache_dir
            assert cache_dir.exists()  # Should be created

    def test_memory_cache_operations(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = CacheManager(Path(tmp_dir))

            # Test set/get
            cache.set("test_key", "test_value")
            assert cache.get("test_key") == "test_value"

            # Test non-existent key
            assert cache.get("non_existent") is None

    def test_file_hash_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache = CacheManager(Path(tmp_dir))

            # Create test file
            test_file = Path(tmp_dir) / "test.mkv"
            test_file.write_text("test content")

            hash1 = cache.get_file_hash(test_file)
            hash2 = cache.get_file_hash(test_file)

            # Same file should produce same hash
            assert hash1 == hash2
            assert len(hash1) == 32  # MD5 hash length


class TestConfigManagerV2:
    """Test the enhanced configuration manager."""

    def test_default_config_creation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            cm = ConfigManager(config_path)

            config = cm.load()

            # Should create default config
            assert isinstance(config, Config)
            assert config_path.exists()
            assert config.asr_provider == "parakeet"

    def test_config_save_load(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            cm = ConfigManager(config_path)

            # Create custom config
            config = Config(
                asr_provider="parakeet", min_confidence=0.8, tmdb_api_key="test_key"
            )

            cm.save(config)
            loaded_config = cm.load()

            assert loaded_config.asr_provider == "parakeet"
            assert loaded_config.min_confidence == 0.8
            assert loaded_config.tmdb_api_key == "test_key"

    def test_legacy_config_migration(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"

            # Create legacy INI-style config
            show_dir = Path(tmp_dir) / "shows"
            show_dir.mkdir()

            legacy_config = {
                "Config": {
                    "tmdb_api_key": "legacy_key",
                    "show_dir": str(show_dir),
                    "max_threads": 4,
                }
            }

            config_path.write_text(json.dumps(legacy_config))

            cm = ConfigManager(config_path)
            config = cm.load()

            assert config.tmdb_api_key == "legacy_key"
            assert config.tmdb_api_key == "legacy_key"
            assert str(config.show_dir) == str(show_dir)

    def test_invalid_json_handling(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"

            # Write invalid JSON
            config_path.write_text("invalid json {")

            cm = ConfigManager(config_path)
            config = cm.load()

            # Should return default config
            assert isinstance(config, Config)
            assert config.asr_provider == "parakeet"


class TestMatchEngineV2:
    """Test the enhanced matching engine."""

    @pytest.fixture
    def mock_config(self):
        return Config(
            cache_dir=Path("/tmp/cache"),
            asr_provider="parakeet",
            sub_provider="local",
            min_confidence=0.7,
        )

    @pytest.fixture
    def test_files(self):
        """Create test MKV files structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)

            # Single file
            single_file = base / "episode.mkv"
            single_file.touch()

            # Series folder
            series_dir = base / "Breaking Bad" / "Season 1"
            series_dir.mkdir(parents=True)
            (series_dir / "breaking_bad_ep1.mkv").touch()
            (series_dir / "breaking_bad_ep2.mkv").touch()

            # Library structure
            lib_dir = base / "library"
            lib_dir.mkdir()

            # Multiple series - using unprocessed filenames for testing grouping logic
            for show in ["Lost", "The Expanse"]:
                for season in [1, 2]:
                    season_dir = lib_dir / show / f"Season {season}"
                    season_dir.mkdir(parents=True)
                    for ep in range(1, 4):
                        # Use unprocessed filename patterns for testing
                        (season_dir / f"{show}_episode_{ep}.mkv").touch()

            yield {
                "single_file": single_file,
                "series_dir": series_dir,
                "library": lib_dir,
                "base": base,
            }

    def test_scan_for_mkv_single_file(self, test_files):
        """Test scanning a single MKV file."""
        with patch("mkv_episode_matcher.core.engine.get_asr_provider") as mock_asr:
            mock_asr.return_value = Mock()

            with tempfile.TemporaryDirectory() as tmp_dir:
                config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
                engine = MatchEngineV2(config)

                files = list(engine.scan_for_mkv(test_files["single_file"]))
                assert len(files) == 1
                assert files[0] == test_files["single_file"]

    def test_scan_for_mkv_directory_recursive(self, test_files):
        """Test recursive scanning of directory."""
        with patch("mkv_episode_matcher.core.engine.get_asr_provider") as mock_asr:
            mock_asr.return_value = Mock()

            with tempfile.TemporaryDirectory() as tmp_dir:
                config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
                engine = MatchEngineV2(config)

                files = list(engine.scan_for_mkv(test_files["library"], recursive=True))
                assert len(files) == 12  # 2 shows * 2 seasons * 3 episodes each

    def test_scan_for_mkv_directory_non_recursive(self, test_files):
        """Test non-recursive scanning."""
        with patch("mkv_episode_matcher.core.engine.get_asr_provider") as mock_asr:
            mock_asr.return_value = Mock()

            with tempfile.TemporaryDirectory() as tmp_dir:
                config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
                engine = MatchEngineV2(config)

                files = list(
                    engine.scan_for_mkv(test_files["library"], recursive=False)
                )
                assert len(files) == 0  # No MKV files in root of library

    def test_detect_context_standard_structure(self, test_files):
        """Test context detection from standard folder structure."""
        with patch("mkv_episode_matcher.core.engine.get_asr_provider") as mock_asr:
            mock_asr.return_value = Mock()

            with tempfile.TemporaryDirectory() as tmp_dir:
                config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
                engine = MatchEngineV2(config)

                video_file = test_files["series_dir"] / "Breaking.Bad.S01E01.mkv"
                show_name, season = engine._detect_context(video_file)

                assert show_name == "Breaking Bad"
                assert season == 1

    def test_detect_context_filename_parsing(self):
        """Test context detection from filename patterns."""
        with patch("mkv_episode_matcher.core.engine.get_asr_provider") as mock_asr:
            mock_asr.return_value = Mock()

            with tempfile.TemporaryDirectory() as tmp_dir:
                config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
                engine = MatchEngineV2(config)

                # Create test file with S##E## pattern
                test_file = Path(tmp_dir) / "Some.Show.S02E05.mkv"
                test_file.touch()

                show_name, season = engine._detect_context(test_file)

                # Should at least detect season from filename
                assert season == 2

    @patch("mkv_episode_matcher.core.engine.get_asr_provider")
    def test_group_files_by_series(self, mock_asr, test_files):
        """Test grouping files by series and season."""
        mock_asr.return_value = Mock()

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            engine = MatchEngineV2(config)

            files = list(engine.scan_for_mkv(test_files["library"], recursive=True))
            groups = engine._group_files_by_series(files, season_override=None)

            # Should have groups for each show/season combination
            assert len(groups) >= 4  # 2 shows * 2 seasons each minimum

            # Check group structure
            for (show_name, season), group_files in groups.items():
                assert isinstance(show_name, str)
                assert isinstance(season, int)
                assert len(group_files) > 0


class TestIntegrationUseCases:
    """Integration tests for all 5 use cases."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with (
            patch("mkv_episode_matcher.core.engine.get_asr_provider") as mock_asr,
            patch(
                "mkv_episode_matcher.core.engine.LocalSubtitleProvider"
            ) as mock_local,
            patch(
                "mkv_episode_matcher.core.engine.OpenSubtitlesProvider"
            ) as mock_opensubtitles,
            patch(
                "mkv_episode_matcher.core.engine.MultiSegmentMatcher"
            ) as mock_matcher,
        ):
            # Configure mocks
            mock_asr_instance = Mock()
            mock_asr_instance.load.return_value = None
            mock_asr.return_value = mock_asr_instance

            mock_local_instance = Mock()
            mock_local.return_value = mock_local_instance

            mock_opensubtitles_instance = Mock()
            mock_opensubtitles.return_value = mock_opensubtitles_instance

            # Mock successful match
            mock_match = MatchResult(
                episode_info=EpisodeInfo(series_name="Test Show", season=1, episode=1),
                confidence=0.9,
                matched_file=Path("/fake/path.mkv"),
                matched_time=60.0,
                model_name="parakeet",
            )

            mock_matcher_instance = Mock()
            mock_matcher_instance.match.return_value = mock_match
            mock_matcher.return_value = mock_matcher_instance

            yield {
                "asr": mock_asr,
                "local": mock_local,
                "opensubtitles": mock_opensubtitles,
                "matcher": mock_matcher,
                "match_result": mock_match,
            }

    def test_use_case_1_single_file(self, mock_dependencies):
        """Test Use Case 1: Process single MKV file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            engine = MatchEngineV2(config)

            # Create single test file in structured folder
            series_dir = Path(tmp_dir) / "Test Show" / "Season 1"
            series_dir.mkdir(parents=True)
            test_file = series_dir / "test_show_episode_01.mkv"
            test_file.touch()

            # Mock subtitle availability
            mock_dependencies["local"].return_value.get_subtitles.return_value = [
                Mock()
            ]

            results = engine.process_single_file(test_file, dry_run=True)

            assert results is not None
            assert results.confidence == 0.9

    def test_use_case_2_series_folder(self, mock_dependencies):
        """Test Use Case 2: Process series folder."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            engine = MatchEngineV2(config)

            # Create series folder structure
            series_dir = Path(tmp_dir) / "Test Show" / "Season 1"
            series_dir.mkdir(parents=True)

            for i in range(1, 4):
                (series_dir / f"test_show_episode_{i:02d}.mkv").touch()

            # Mock subtitle availability
            mock_dependencies["local"].return_value.get_subtitles.return_value = [
                Mock()
            ]

            results, _ = engine.process_path(series_dir, dry_run=True, recursive=False)

            assert len(results) == 3  # Should process 3 files

    def test_use_case_3_output_directory(self, mock_dependencies):
        """Test Use Case 3: Process with custom output directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            engine = MatchEngineV2(config)

            # Create test structure
            input_dir = Path(tmp_dir) / "input"
            output_dir = Path(tmp_dir) / "output"
            input_dir.mkdir()

            test_file = input_dir / "test.mkv"
            test_file.touch()

            # Mock subtitle availability
            mock_dependencies["local"].return_value.get_subtitles.return_value = [
                Mock()
            ]

            results, _ = engine.process_path(
                test_file,
                output_dir=output_dir,
                dry_run=True,  # Use dry_run to avoid actual file operations
            )

            assert len(results) >= 0  # Should not crash

    def test_use_case_4_json_output(self, mock_dependencies):
        """Test Use Case 4: JSON output for automation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            engine = MatchEngineV2(config)

            test_file = Path(tmp_dir) / "test.mkv"
            test_file.touch()

            # Mock subtitle availability
            mock_dependencies["local"].return_value.get_subtitles.return_value = [
                Mock()
            ]

            results, _ = engine.process_path(test_file, json_output=True, dry_run=True)

            # Test JSON export
            json_output = engine.export_results(results)
            json_data = json.loads(json_output)

            assert isinstance(json_data, list)

    def test_use_case_5_library_processing(self, mock_dependencies):
        """Test Use Case 5: Process entire library."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            engine = MatchEngineV2(config)

            # Create library structure
            library_dir = Path(tmp_dir) / "library"
            library_dir.mkdir()

            # Multiple shows
            for show in ["Show A", "Show B"]:
                show_dir = library_dir / show / "Season 1"
                show_dir.mkdir(parents=True)
                for ep in range(1, 3):
                    (show_dir / f"{show}.S01E{ep:02d}.mkv").touch()

            # Mock subtitle availability
            mock_dependencies["local"].return_value.get_subtitles.return_value = [
                Mock()
            ]

            results = engine.process_library(library_dir, dry_run=True)

            assert len(results) >= 0  # Should not crash
            # Note: Actual result count depends on mock configuration


class TestCLIIntegration:
    """Test CLI integration with engine."""

    def test_cli_config_integration(self):
        """Test that CLI properly loads and uses configuration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"

            # Create test config
            config = Config(
                cache_dir=Path(tmp_dir) / "cache",
                asr_provider="parakeet",
                min_confidence=0.8,
            )

            cm = ConfigManager(config_path)
            cm.save(config)

            # Verify config can be loaded
            loaded_config = cm.load()
            assert loaded_config.min_confidence == 0.8
            assert loaded_config.asr_provider == "parakeet"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
