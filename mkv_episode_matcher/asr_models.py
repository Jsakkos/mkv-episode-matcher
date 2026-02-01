"""
ASR Model Abstraction Layer

This module provides a unified interface for different Automatic Speech Recognition models,
supporting OpenAI Whisper models via faster-whisper for efficient inference.
"""

import abc
import os
import re
import tempfile
from pathlib import Path

import ctranslate2
import librosa
import numpy as np
import soundfile as sf
from loguru import logger
from rapidfuzz import fuzz

# Cache for loaded models to avoid reloading
_model_cache = {}


class ASRModel(abc.ABC):
    """Abstract base class for ASR models."""

    def __init__(self, model_name: str, device: str | None = None):
        """
        Initialize ASR model.

        Args:
            model_name: Name/identifier of the model
            device: Device to run on ('cpu', 'cuda', or None for auto-detect)
        """
        self.model_name = model_name
        self.device = device or self._get_default_device()
        self._model = None

    def _get_default_device(self) -> str:
        """Get default device for this model type."""
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
        return "cpu"

    @abc.abstractmethod
    def load(self):
        """Load the model. Should be called before transcription."""
        pass

    @abc.abstractmethod
    def transcribe(self, audio_path: str | Path) -> dict:
        """
        Transcribe audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with at least 'text' key containing transcription
        """
        pass

    def calculate_match_score(self, transcription: str, reference: str) -> float:
        """
        Calculate similarity score between transcription and reference.

        Args:
            transcription: Transcribed text
            reference: Reference subtitle text

        Returns:
            Float score between 0.0 and 1.0
        """
        # Default implementation: Standard weights
        # Token sort ratio (70%) + Partial ratio (30%)
        token_weight = 0.7
        partial_weight = 0.3

        score = (
            fuzz.token_sort_ratio(transcription, reference) * token_weight
            + fuzz.partial_ratio(transcription, reference) * partial_weight
        ) / 100.0

        return score

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def unload(self):
        """Unload model to free memory."""
        self._model = None


class FasterWhisperModel(ASRModel):
    """
    OpenAI Whisper ASR model implementation using faster-whisper.

    This uses CTranslate2 for efficient inference, providing:
    - Faster inference than original Whisper
    - Lower memory usage
    - Easy CPU and GPU support
    - No complex dependencies (unlike NVIDIA NeMo)
    """

    # Available model sizes with their approximate properties
    MODEL_SIZES = {
        "tiny": {"params": "39M", "vram": "~1GB", "speed": "fastest"},
        "tiny.en": {"params": "39M", "vram": "~1GB", "speed": "fastest"},
        "base": {"params": "74M", "vram": "~1GB", "speed": "fast"},
        "base.en": {"params": "74M", "vram": "~1GB", "speed": "fast"},
        "small": {"params": "244M", "vram": "~2GB", "speed": "medium"},
        "small.en": {"params": "244M", "vram": "~2GB", "speed": "medium"},
        "medium": {"params": "769M", "vram": "~5GB", "speed": "slow"},
        "medium.en": {"params": "769M", "vram": "~5GB", "speed": "slow"},
        "large-v3": {"params": "1550M", "vram": "~10GB", "speed": "slowest"},
    }

    def __init__(
        self, model_name: str = "small", device: str | None = None
    ):
        """
        Initialize Faster Whisper model.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large-v3)
            device: Device to run on ('cpu', 'cuda', or None for auto-detect)
        """
        # Normalize model name
        if model_name.startswith("openai/whisper-"):
            model_name = model_name.replace("openai/whisper-", "")
        
        super().__init__(model_name, device)

    def _get_compute_type(self) -> str:
        """Get optimal compute type for the device."""
        if self.device == "cuda":
            # Use float16 for GPU (faster and lower memory)
            return "float16"
        else:
            # Use int8 for CPU (good balance of speed and accuracy)
            return "int8"

    def load(self):
        """Load Faster Whisper model with caching."""
        if self.is_loaded:
            return

        cache_key = f"faster_whisper_{self.model_name}_{self.device}"

        if cache_key in _model_cache:
            self._model = _model_cache[cache_key]
            logger.debug(
                f"Using cached Faster Whisper model: {self.model_name} on {self.device}"
            )
            return

        try:
            from faster_whisper import WhisperModel

            compute_type = self._get_compute_type()
            
            logger.info(
                f"Loading Faster Whisper model: {self.model_name} on {self.device} "
                f"(compute_type={compute_type})"
            )

            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=compute_type,
                download_root=None,  # Use default cache location
            )

            _model_cache[cache_key] = self._model
            logger.info(
                f"Loaded Faster Whisper model: {self.model_name} on {self.device}"
            )

        except ImportError as e:
            raise ImportError(
                "faster-whisper not installed. Run: pip install faster-whisper"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load Faster Whisper model {self.model_name}: {e}")
            raise

    def _preprocess_audio(self, audio_path: str | Path) -> str:
        """
        Preprocess audio for Whisper model requirements.

        Args:
            audio_path: Path to input audio file

        Returns:
            Path to preprocessed audio file (or original if no preprocessing needed)
        """
        try:
            # Load audio with librosa
            audio, original_sr = librosa.load(str(audio_path), sr=None)

            # Target sample rate for Whisper models (16kHz)
            target_sr = 16000

            # Resample if necessary
            if original_sr != target_sr:
                audio = librosa.resample(
                    audio, orig_sr=original_sr, target_sr=target_sr
                )
                logger.debug(f"Resampled audio from {original_sr}Hz to {target_sr}Hz")

            # Normalize audio to [-1, 1] range
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio))

            # Create temporary file for preprocessed audio
            temp_dir = Path(tempfile.gettempdir()) / "whisper_preprocessed"
            temp_dir.mkdir(exist_ok=True)

            temp_audio_path = temp_dir / f"preprocessed_{Path(audio_path).stem}.wav"

            # Save preprocessed audio
            sf.write(str(temp_audio_path), audio, target_sr)

            logger.debug(f"Preprocessed audio saved to {temp_audio_path}")
            return str(temp_audio_path)

        except Exception as e:
            logger.warning(f"Audio preprocessing failed, using original: {e}")
            return str(audio_path)

    def _clean_transcription_text(self, text: str) -> str:
        """
        Clean and normalize transcription text.

        Args:
            text: Raw transcription text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Use same cleaning logic as EpisodeMatcher.clean_text()
        text = text.lower().strip()
        text = re.sub(r"\[.*?\]|\<.*?\>", "", text)
        text = re.sub(r"([A-Za-z])-\1+", r"\1", text)
        return " ".join(text.split())

    def transcribe(self, audio_path: str | Path) -> dict:
        """
        Transcribe audio using Faster Whisper.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with 'text', 'raw_text', 'segments', and 'language'
        """
        if not self.is_loaded:
            self.load()

        preprocessed_audio = None
        try:
            logger.debug(f"Starting Faster Whisper transcription for {audio_path}")

            # Preprocess audio
            preprocessed_audio = self._preprocess_audio(audio_path)

            # Transcribe with faster-whisper
            segments, info = self._model.transcribe(
                preprocessed_audio,
                language="en",  # Force English for TV episode matching
                beam_size=5,
                best_of=5,
                temperature=0.0,  # Greedy decoding for consistency
                condition_on_previous_text=False,
                vad_filter=True,  # Filter out non-speech
            )

            # Collect all segment texts
            segment_list = []
            full_text_parts = []
            
            for segment in segments:
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                })
                full_text_parts.append(segment.text)

            raw_text = " ".join(full_text_parts).strip()
            cleaned_text = self._clean_transcription_text(raw_text)

            logger.debug(f"Raw transcription: '{raw_text}'")
            logger.debug(f"Cleaned transcription: '{cleaned_text}'")

            return {
                "text": cleaned_text,
                "raw_text": raw_text,
                "segments": segment_list,
                "language": info.language if hasattr(info, 'language') else "en",
            }

        except Exception as e:
            logger.error(
                f"Faster Whisper transcription failed for {audio_path}: {type(e).__name__}: {e}"
            )
            import traceback
            traceback.print_exc()
            # Return empty result instead of raising to allow fallback
            return {"text": "", "raw_text": "", "segments": [], "language": "en"}
        finally:
            # Clean up preprocessed audio file
            if preprocessed_audio and preprocessed_audio != str(audio_path):
                try:
                    Path(preprocessed_audio).unlink(missing_ok=True)
                except Exception as e:
                    logger.debug(f"Failed to clean up preprocessed audio: {e}")


def create_asr_model(model_config: dict) -> ASRModel:
    """
    Factory function to create ASR models from configuration.

    Args:
        model_config: Dictionary with 'type' and 'name' keys

    Returns:
        Configured ASRModel instance

    Example:
        model_config = {"type": "whisper", "name": "small"}
        model = create_asr_model(model_config)
    """
    model_type = model_config.get("type", "").lower()
    model_name = model_config.get("name", "")
    device = model_config.get("device")

    # Handle whisper and faster-whisper types
    if model_type in ("whisper", "faster-whisper", "openai-whisper"):
        if not model_name:
            model_name = "small"
        
        logger.info(f"Creating Faster Whisper model: {model_name}")
        return FasterWhisperModel(model_name, device)
    
    # Legacy parakeet support - redirect to whisper
    elif model_type == "parakeet":
        logger.warning(
            "Parakeet models are no longer supported. Using Whisper 'small' model instead."
        )
        return FasterWhisperModel("small", device)
    
    else:
        raise ValueError(
            f"Unsupported model type: {model_type}. Supported types: 'whisper', 'faster-whisper'"
        )


def get_cached_model(model_config: dict) -> ASRModel:
    """
    Get a cached model instance, creating it if necessary.

    Args:
        model_config: Dictionary with model configuration

    Returns:
        ASRModel instance (loaded and ready for use)
    """
    cache_key = f"{model_config.get('type', '')}_{model_config.get('name', '')}_{model_config.get('device', 'auto')}"

    if cache_key not in _model_cache:
        model = create_asr_model(model_config)
        model.load()  # Load immediately for caching
        _model_cache[cache_key] = model

    return _model_cache[cache_key]


def clear_model_cache():
    """Clear all cached models to free memory."""
    global _model_cache
    for model in _model_cache.values():
        if hasattr(model, "unload"):
            model.unload()
    _model_cache.clear()
    logger.info("Cleared ASR model cache")


def list_available_models() -> dict:
    """
    List available model types and their requirements.

    Returns:
        Dictionary with model types and their availability status
    """
    availability = {}

    # Check Faster Whisper availability
    try:
        import faster_whisper  # noqa: F401

        availability["whisper"] = {
            "available": True,
            "models": list(FasterWhisperModel.MODEL_SIZES.keys()),
            "default": "small",
            "description": "OpenAI Whisper models via faster-whisper (CTranslate2)",
        }
    except ImportError:
        availability["whisper"] = {
            "available": False,
            "error": "faster-whisper not installed. Run: pip install faster-whisper",
        }

    return availability
