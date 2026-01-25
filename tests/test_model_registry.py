"""
Tests for the ASR model registry.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from mkv_episode_matcher.core.model_registry import (
    get_model_info,
    list_recommended_models,
    get_default_model,
    get_leaderboard_url,
    is_model_downloaded,
    get_models_for_hardware,
    RECOMMENDED_MODELS,
    DEFAULT_MODEL,
)


class TestModelRegistry:
    """Test the model registry functions."""

    def test_get_model_info_known_model(self):
        """Test getting info for a known model."""
        info = get_model_info("small")
        assert info is not None
        assert info["name"] == "Whisper Small"
        assert info["size_mb"] == 465
        assert info["requires_gpu"] is False

    def test_get_model_info_unknown_model(self):
        """Test getting info for an unknown model."""
        info = get_model_info("some-unknown-model")
        assert info is None

    def test_list_recommended_models(self):
        """Test listing all recommended models."""
        models = list_recommended_models()
        assert len(models) >= 5
        assert "small" in models
        assert "base" in models
        assert "tiny" in models

    def test_get_default_model(self):
        """Test getting the default model."""
        default = get_default_model()
        assert default == "small"

    def test_get_leaderboard_url(self):
        """Test getting the leaderboard URL."""
        url = get_leaderboard_url()
        assert "huggingface.co" in url
        assert "open_asr_leaderboard" in url

    def test_is_model_downloaded_handles_missing_cache(self):
        """Test that is_model_downloaded handles missing cache gracefully."""
        with patch.object(Path, "exists", return_value=False):
            result = is_model_downloaded("small")
            assert result is False

    def test_get_models_for_hardware_cpu_only(self):
        """Test hardware-based model recommendations for CPU."""
        models = get_models_for_hardware(has_gpu=False, vram_gb=0)
        # Should only include CPU-friendly models
        for model in models:
            info = get_model_info(model)
            assert info is not None
            assert info["requires_gpu"] is False

    def test_get_models_for_hardware_with_gpu(self):
        """Test hardware-based model recommendations with GPU."""
        models = get_models_for_hardware(has_gpu=True, vram_gb=12)
        # Should include more models than CPU-only
        cpu_models = get_models_for_hardware(has_gpu=False, vram_gb=0)
        assert len(models) > len(cpu_models)


class TestModelRegistryIntegration:
    """Integration tests for model registry with config."""

    def test_default_model_in_recommended_models(self):
        """Ensure default model is in the recommended list."""
        models = list_recommended_models()
        assert DEFAULT_MODEL in models

    def test_all_models_have_required_fields(self):
        """Verify all models have required metadata fields."""
        required_fields = [
            "name",
            "size_mb",
            "requires_gpu",
            "quality",
            "speed",
            "description",
        ]
        for model_name, model_info in RECOMMENDED_MODELS.items():
            for field in required_fields:
                assert field in model_info, f"Model {model_name} missing field {field}"

    def test_quality_values_are_valid(self):
        """Verify all quality values are valid."""
        valid_qualities = {"basic", "good", "better", "best"}
        for model_name, model_info in RECOMMENDED_MODELS.items():
            assert (
                model_info["quality"] in valid_qualities
            ), f"Model {model_name} has invalid quality"
