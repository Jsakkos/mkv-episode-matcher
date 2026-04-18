"""Regression tests for PR #94 fixes.

Covers:
- Parakeet -> whisper migration never carries incompatible parakeet model ids forward
  (both the Pydantic model validator and the legacy INI ConfigManager migration).
- `_get_default_device()` falls back on ctranslate2's CUDA count without re-implementing
  `CUDA_VISIBLE_DEVICES` handling.
- Backend `get_engine()` reads config via `ConfigManager.load()`, not `manager.config`.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from mkv_episode_matcher.core.config_manager import ConfigManager
from mkv_episode_matcher.core.models import Config


class TestMigrateAsrProviderValidator:
    """`Config.migrate_asr_provider` must not smuggle parakeet model names into whisper."""

    def test_parakeet_with_nvidia_model_id_resets_to_small(self):
        config = Config(
            asr_provider="parakeet",
            asr_model_name="nvidia/parakeet-tdt-0.6b-v2",
        )
        assert config.asr_provider == "whisper"
        assert config.asr_model_name == "small"

    def test_parakeet_with_empty_model_name_resets_to_small(self):
        config = Config(asr_provider="parakeet", asr_model_name="")
        assert config.asr_provider == "whisper"
        assert config.asr_model_name == "small"

    def test_whisper_provider_preserves_model_name(self):
        config = Config(asr_provider="whisper", asr_model_name="medium.en")
        assert config.asr_provider == "whisper"
        assert config.asr_model_name == "medium.en"


class TestLegacyIniMigration:
    """`ConfigManager._migrate_legacy_config` must reset model name when source is parakeet."""

    def _load_with_legacy(self, legacy: dict) -> Config:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(json.dumps({"Config": legacy}))
            return ConfigManager(config_path).load()

    def test_legacy_parakeet_model_name_is_reset(self):
        config = self._load_with_legacy({
            "asr_provider": "parakeet",
            "asr_model_name": "nvidia/parakeet-tdt-0.6b-v2",
        })
        assert config.asr_provider == "whisper"
        assert config.asr_model_name == "small"

    def test_legacy_whisper_model_name_is_preserved(self):
        config = self._load_with_legacy({
            "asr_provider": "whisper",
            "asr_model_name": "medium.en",
        })
        assert config.asr_provider == "whisper"
        assert config.asr_model_name == "medium.en"

    def test_legacy_missing_provider_defaults_to_whisper_and_preserves_model(self):
        config = self._load_with_legacy({"asr_model_name": "base"})
        assert config.asr_provider == "whisper"
        assert config.asr_model_name == "base"


class TestGetDefaultDevice:
    """`ASRModel._get_default_device` should trust ctranslate2 for CUDA detection."""

    def test_returns_cuda_when_device_count_positive(self):
        from mkv_episode_matcher import asr_models

        with patch.object(asr_models.ctranslate2, "get_cuda_device_count", return_value=1):
            model = asr_models.FasterWhisperModel(model_name="small", device=None)
            assert model.device == "cuda"

    def test_returns_cpu_when_device_count_zero(self):
        from mkv_episode_matcher import asr_models

        with patch.object(asr_models.ctranslate2, "get_cuda_device_count", return_value=0):
            model = asr_models.FasterWhisperModel(model_name="small", device=None)
            assert model.device == "cpu"

    def test_returns_cpu_when_ctranslate2_raises(self):
        from mkv_episode_matcher import asr_models

        with patch.object(
            asr_models.ctranslate2,
            "get_cuda_device_count",
            side_effect=RuntimeError("driver missing"),
        ):
            model = asr_models.FasterWhisperModel(model_name="small", device=None)
            assert model.device == "cpu"

    def test_cuda_visible_devices_empty_string_yields_cpu_via_ctranslate2(self, monkeypatch):
        """ctranslate2 already returns 0 devices when CUDA_VISIBLE_DEVICES="";
        exercising that path ensures we don't re-introduce the env-var check."""
        from mkv_episode_matcher import asr_models

        monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
        with patch.object(asr_models.ctranslate2, "get_cuda_device_count", return_value=0):
            model = asr_models.FasterWhisperModel(model_name="small", device=None)
            assert model.device == "cpu"

    def test_cuda_visible_devices_unset_does_not_force_cpu(self, monkeypatch):
        """Regression: previous PR forced CPU when CUDA_VISIBLE_DEVICES was unset."""
        from mkv_episode_matcher import asr_models

        monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
        with patch.object(asr_models.ctranslate2, "get_cuda_device_count", return_value=1):
            model = asr_models.FasterWhisperModel(model_name="small", device=None)
            assert model.device == "cuda"


class TestBackendDependenciesConfigLoad:
    """`get_engine()` must call `ConfigManager.load()` instead of reading `manager.config`."""

    def test_get_engine_calls_manager_load(self):
        import mkv_episode_matcher.backend.dependencies as deps

        # Reset singleton state for isolation
        deps._engine_instance = None
        deps._parsing_status = "idle"

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = Config(cache_dir=Path(tmp_dir), sub_provider="local")
            fake_manager = Mock()
            fake_manager.load.return_value = config

            with patch.object(deps, "get_config_manager", return_value=fake_manager), \
                 patch.object(deps, "MatchEngineV2") as mock_engine_cls:
                mock_engine_cls.return_value = Mock()
                deps.get_engine()

            fake_manager.load.assert_called_once()
            mock_engine_cls.assert_called_once_with(config)

        # Clean up singleton so other tests get a fresh state
        deps._engine_instance = None
        deps._parsing_status = "idle"
