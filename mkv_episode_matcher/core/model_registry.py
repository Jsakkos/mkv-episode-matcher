"""
ASR Model Registry

Provides a curated list of recommended Whisper ASR models with metadata
for hardware requirements, quality, and performance characteristics.

For more models, see: https://huggingface.co/spaces/hf-audio/open_asr_leaderboard
"""

from pathlib import Path
from typing import TypedDict

from loguru import logger

# HuggingFace leaderboard URL for users to explore more models
LEADERBOARD_URL = "https://huggingface.co/spaces/hf-audio/open_asr_leaderboard"

# Default model - lightweight, works on CPU
DEFAULT_MODEL = "small"


class ModelInfo(TypedDict):
    """Type definition for model metadata."""

    name: str
    size_mb: int
    requires_gpu: bool
    quality: str  # "good", "better", "best"
    speed: str  # "fast", "medium", "slow"
    description: str


# Curated list of Whisper models via faster-whisper
RECOMMENDED_MODELS: dict[str, ModelInfo] = {
    "tiny": {
        "name": "Whisper Tiny",
        "size_mb": 75,
        "requires_gpu": False,
        "quality": "basic",
        "speed": "fastest",
        "description": "Fastest model. Good for testing and quick prototyping.",
    },
    "tiny.en": {
        "name": "Whisper Tiny (English)",
        "size_mb": 75,
        "requires_gpu": False,
        "quality": "basic",
        "speed": "fastest",
        "description": "English-only tiny model. Slightly better accuracy for English.",
    },
    "base": {
        "name": "Whisper Base",
        "size_mb": 145,
        "requires_gpu": False,
        "quality": "good",
        "speed": "fast",
        "description": "Good balance of speed and accuracy for CPU.",
    },
    "base.en": {
        "name": "Whisper Base (English)",
        "size_mb": 145,
        "requires_gpu": False,
        "quality": "good",
        "speed": "fast",
        "description": "English-only base model. Better accuracy for English content.",
    },
    "small": {
        "name": "Whisper Small",
        "size_mb": 465,
        "requires_gpu": False,
        "quality": "better",
        "speed": "medium",
        "description": "Recommended default. Good accuracy, works on CPU.",
    },
    "small.en": {
        "name": "Whisper Small (English)",
        "size_mb": 465,
        "requires_gpu": False,
        "quality": "better",
        "speed": "medium",
        "description": "English-only small model. Best balance for English TV content.",
    },
    "medium": {
        "name": "Whisper Medium",
        "size_mb": 1500,
        "requires_gpu": True,
        "quality": "best",
        "speed": "slow",
        "description": "High accuracy. GPU recommended for reasonable speed.",
    },
    "medium.en": {
        "name": "Whisper Medium (English)",
        "size_mb": 1500,
        "requires_gpu": True,
        "quality": "best",
        "speed": "slow",
        "description": "English-only medium model. Best accuracy for English content.",
    },
    "large-v3": {
        "name": "Whisper Large v3",
        "size_mb": 3000,
        "requires_gpu": True,
        "quality": "best",
        "speed": "slowest",
        "description": "Highest accuracy. Requires GPU with 10GB+ VRAM.",
    },
}


def get_model_info(model_name: str) -> ModelInfo | None:
    """
    Get metadata for a model by name.

    Args:
        model_name: Model name (e.g., "small", "base.en")

    Returns:
        ModelInfo dict if known, None if custom/unknown model
    """
    return RECOMMENDED_MODELS.get(model_name)


def list_recommended_models() -> dict[str, ModelInfo]:
    """
    List all curated recommended models.

    Returns:
        Dictionary of model_name -> ModelInfo
    """
    return RECOMMENDED_MODELS.copy()


def get_default_model() -> str:
    """Get the default model name."""
    return DEFAULT_MODEL


def get_leaderboard_url() -> str:
    """Get the HuggingFace ASR leaderboard URL for browsing more models."""
    return LEADERBOARD_URL


def is_model_downloaded(model_name: str) -> bool:
    """
    Check if a model has been downloaded to the HuggingFace cache.

    Args:
        model_name: Whisper model name (e.g., "small", "base.en")

    Returns:
        True if model appears to be cached locally
    """
    try:
        # faster-whisper models are cached in ~/.cache/huggingface/hub
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

        if not cache_dir.exists():
            return False

        # Check for ctranslate2 whisper models
        # They are stored as "models--Systran--faster-whisper-{model_name}"
        sanitized_name = f"models--Systran--faster-whisper-{model_name}"

        model_cache = cache_dir / sanitized_name
        return model_cache.exists()

    except Exception as e:
        logger.debug(f"Error checking model cache: {e}")
        return False


def get_models_for_hardware(has_gpu: bool = False, vram_gb: int = 0) -> list[str]:
    """
    Get recommended models based on available hardware.

    Args:
        has_gpu: Whether a CUDA GPU is available
        vram_gb: Amount of GPU VRAM in GB (0 if no GPU)

    Returns:
        List of recommended model names, ordered by preference
    """
    recommendations = []

    for model_name, info in RECOMMENDED_MODELS.items():
        if info["requires_gpu"] and not has_gpu:
            continue

        # Large models need more VRAM
        if info["size_mb"] > 2000 and vram_gb < 10:
            continue
        elif info["size_mb"] > 1000 and vram_gb < 6:
            continue

        recommendations.append(model_name)

    # Sort by quality (best first), then by speed (fast first)
    quality_order = {"best": 0, "better": 1, "good": 2, "basic": 3}
    speed_order = {"fastest": 0, "fast": 1, "medium": 2, "slow": 3, "slowest": 4}

    recommendations.sort(
        key=lambda m: (
            quality_order.get(RECOMMENDED_MODELS[m]["quality"], 4),
            speed_order.get(RECOMMENDED_MODELS[m]["speed"], 4),
        )
    )

    return recommendations
