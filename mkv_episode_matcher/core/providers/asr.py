import abc
from pathlib import Path
from typing import Any

from loguru import logger

from mkv_episode_matcher.asr_models import (
    ASRModel as _NativeASRModel,
)
from mkv_episode_matcher.asr_models import (
    create_asr_model as _create_native_model,
)


class ASRProvider(abc.ABC):
    """Abstract base class for ASR providers."""

    @abc.abstractmethod
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe the given audio file to text."""
        pass

    @abc.abstractmethod
    def load(self):
        """Prepare/Load the model."""
        pass

    @abc.abstractmethod
    def calculate_match_score(self, transcription: str, reference: str) -> float:
        """Calculate similarity score."""
        pass


class NativeASRProvider(ASRProvider):
    """Wrapper around the existing native ASR models (Whisper, Parakeet)."""

    def __init__(self, model_config: dict[str, Any]):
        self._model: _NativeASRModel = _create_native_model(model_config)
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            logger.info(f"Loading ASR model: {self._model.model_name}")
            self._model.load()
            self._loaded = True

    def load(self):
        self._ensure_loaded()

    def transcribe(self, audio_path: Path) -> str:
        self._ensure_loaded()
        result = self._model.transcribe(audio_path)
        return result.get("text", "")  # type: ignore

    def calculate_match_score(self, transcription: str, reference: str) -> float:
        return self._model.calculate_match_score(transcription, reference)


factory_memo = {}


def get_asr_provider(
    model_type: str = "parakeet",
    model_name: str | None = None,
    device: str | None = None,
) -> ASRProvider:
    """Factory to get or create an ASR provider."""
    # Set default match names based on type if not provided
    if not model_name:
        if model_type == "whisper" or model_type == "faster-whisper":
            model_name = "base.en"
        elif "parakeet" in model_type:
            model_name = "nvidia/parakeet-ctc-0.6b"

    key = (model_type, model_name, device)
    if key in factory_memo:
        return factory_memo[key]

    config = {"type": model_type, "name": model_name}
    if device:
        config["device"] = device

    provider = NativeASRProvider(config)
    factory_memo[key] = provider
    return provider
