"""
ASR Model Registry

Provides a curated list of recommended NeMo-compatible ASR models with metadata
for hardware requirements, quality, and performance characteristics.

For more models, see: https://huggingface.co/spaces/hf-audio/open_asr_leaderboard
"""

from pathlib import Path
from typing import TypedDict

from loguru import logger

# HuggingFace leaderboard URL for users to explore more models
LEADERBOARD_URL = "https://huggingface.co/spaces/hf-audio/open_asr_leaderboard"

# Default model - lightweight, works on CPU
DEFAULT_MODEL = "nvidia/parakeet-ctc-0.6b"


class ModelInfo(TypedDict):
    """Type definition for model metadata."""

    name: str
    size_mb: int
    requires_gpu: bool
    quality: str  # "good", "better", "best"
    speed: str  # "fast", "medium", "slow"
    description: str
    decoder_type: str  # "ctc" or "tdt"


# Curated list of known-compatible NeMo ASR models
RECOMMENDED_MODELS: dict[str, ModelInfo] = {
    "nvidia/parakeet-ctc-0.6b": {
        "name": "Parakeet CTC 0.6B",
        "size_mb": 600,
        "requires_gpu": False,
        "quality": "good",
        "speed": "fast",
        "description": "Default model. Lightweight, works well on CPU.",
        "decoder_type": "ctc",
    },
    "nvidia/parakeet-ctc-1.1b": {
        "name": "Parakeet CTC 1.1B",
        "size_mb": 1100,
        "requires_gpu": True,
        "quality": "better",
        "speed": "medium",
        "description": "Higher accuracy, GPU recommended for speed.",
        "decoder_type": "ctc",
    },
    "nvidia/parakeet-tdt-0.6b-v2": {
        "name": "Parakeet TDT 0.6B v2",
        "size_mb": 600,
        "requires_gpu": True,
        "quality": "better",
        "speed": "medium",
        "description": "TDT decoder, better for noisy audio. Requires GPU.",
        "decoder_type": "tdt",
    },
    "nvidia/parakeet-tdt-1.1b": {
        "name": "Parakeet TDT 1.1B",
        "size_mb": 1100,
        "requires_gpu": True,
        "quality": "best",
        "speed": "slow",
        "description": "Best accuracy. Requires CUDA GPU with 6GB+ VRAM.",
        "decoder_type": "tdt",
    },
}


def get_model_info(model_name: str) -> ModelInfo | None:
    """
    Get metadata for a model by name.

    Args:
        model_name: HuggingFace model ID (e.g., "nvidia/parakeet-ctc-0.6b")

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


def get_decoder_type(model_name: str) -> str:
    """
    Detect decoder type (CTC or TDT) from model name.

    Args:
        model_name: HuggingFace model ID

    Returns:
        "ctc" or "tdt"
    """
    info = get_model_info(model_name)
    if info:
        return info["decoder_type"]

    # Infer from model name for unknown models
    model_lower = model_name.lower()
    if "tdt" in model_lower:
        return "tdt"
    return "ctc"  # Default to CTC


def is_model_downloaded(model_name: str) -> bool:
    """
    Check if a model has been downloaded to the HuggingFace cache.

    Args:
        model_name: HuggingFace model ID

    Returns:
        True if model appears to be cached locally
    """
    try:
        # HuggingFace models are cached in ~/.cache/huggingface/hub
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

        if not cache_dir.exists():
            return False

        # Models are stored with sanitized names
        # e.g., "nvidia/parakeet-ctc-0.6b" -> "models--nvidia--parakeet-ctc-0.6b"
        sanitized_name = f"models--{model_name.replace('/', '--')}"

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

        # TDT models need more VRAM
        if info["decoder_type"] == "tdt" and vram_gb < 6:
            continue

        recommendations.append(model_name)

    # Sort by quality (best first), then by speed (fast first)
    quality_order = {"best": 0, "better": 1, "good": 2}
    speed_order = {"fast": 0, "medium": 1, "slow": 2}

    recommendations.sort(
        key=lambda m: (
            quality_order.get(RECOMMENDED_MODELS[m]["quality"], 3),
            speed_order.get(RECOMMENDED_MODELS[m]["speed"], 3),
        )
    )

    return recommendations
