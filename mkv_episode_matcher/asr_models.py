"""
ASR Model Abstraction Layer

This module provides a unified interface for different Automatic Speech Recognition models,
including OpenAI Whisper and NVIDIA Parakeet models.
"""

import abc
import os
import re
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
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
        return "cuda" if torch.cuda.is_available() else "cpu"

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


class ParakeetTDTModel(ASRModel):
    """
    NVIDIA Parakeet TDT ASR model implementation.

    WARNING: This model (TDT) uses the Transducer decoder which requires significant GPU resources
    and may be unstable on some Windows configurations (CUDA errors).
    """

    def __init__(
        self, model_name: str = "nvidia/parakeet-tdt-0.6b-v2", device: str | None = None
    ):
        """
        Initialize Parakeet TDT model.

        Args:
            model_name: Parakeet model identifier from HuggingFace
            device: Device to run on
        """
        super().__init__(model_name, device)

    def load(self):
        """Load Parakeet model with caching."""
        if self.is_loaded:
            return

        cache_key = f"parakeet_tdt_{self.model_name}_{self.device}"

        if cache_key in _model_cache:
            self._model = _model_cache[cache_key]
            logger.debug(
                f"Using cached Parakeet TDT model: {self.model_name} on {self.device}"
            )
            return

        try:
            # Windows compatibility: Patch signal module before importing NeMo
            if os.name == "nt":  # Windows
                import signal

                if not hasattr(signal, "SIGKILL"):
                    # Add missing signal constants for Windows compatibility
                    signal.SIGKILL = 9
                    signal.SIGTERM = 15

            import nemo.collections.asr as nemo_asr

            # Store original environment variables for restoration
            original_env = {}

            # Configure environment to suppress NeMo warnings and optimize performance
            nemo_env_settings = {
                "NEMO_DISABLE_TRAINING_LOGS": "1",
                "NEMO_DISABLE_HYDRA_LOGS": "1",
                "HYDRA_FULL_ERROR": "0",
                "PYTHONWARNINGS": "ignore::UserWarning",
                "TOKENIZERS_PARALLELISM": "false",  # Avoid tokenizer warnings
            }

            # Windows compatibility: Add optimizations but avoid signal issues
            if os.name == "nt":  # Windows
                nemo_env_settings.update({
                    "OMP_NUM_THREADS": "1",
                    "MKL_NUM_THREADS": "1",
                    "NEMO_BYPASS_SIGNALS": "1",  # Bypass NeMo signal handling on Windows
                })

            for key, value in nemo_env_settings.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                # Set device for NeMo
                if self.device == "cuda" and torch.cuda.is_available():
                    # NeMo will automatically use CUDA if available
                    pass
                elif self.device == "cpu":
                    # Force CPU usage - NeMo respects CUDA_VISIBLE_DEVICES=""
                    original_env["CUDA_VISIBLE_DEVICES"] = os.environ.get(
                        "CUDA_VISIBLE_DEVICES"
                    )
                    os.environ["CUDA_VISIBLE_DEVICES"] = ""

                # Load model with reduced verbosity
                self._model = nemo_asr.models.ASRModel.from_pretrained(
                    model_name=self.model_name,
                    strict=False,  # Allow loading with missing keys to reduce warnings
                )

                # Configure model for optimal inference
                if hasattr(self._model, "set_batch_size"):
                    self._model.set_batch_size(1)  # Optimize for single file processing

                # Fix for Windows: Force num_workers to 0 to avoid multiprocessing errors/locks
                if hasattr(self._model, "cfg"):
                    for ds_config in ["test_ds", "validation_ds"]:
                        if ds_config in self._model.cfg:
                            self._model.cfg[ds_config].num_workers = 0

                if hasattr(self._model, "eval"):
                    self._model.eval()  # Set to evaluation mode

            finally:
                # Restore original environment variables
                for key, original_value in original_env.items():
                    if original_value is not None:
                        os.environ[key] = original_value
                    elif key in os.environ:
                        del os.environ[key]

            _model_cache[cache_key] = self._model
            logger.info(
                f"Loaded Parakeet TDT model: {self.model_name} on {self.device}"
            )

        except ImportError as e:
            raise ImportError(
                "NVIDIA NeMo not installed. Run: pip install nemo_toolkit[asr]"
            ) from e
        except Exception as e:
            logger.error(f"Failed to load Parakeet TDT model {self.model_name}: {e}")
            raise

    def _preprocess_audio(self, audio_path: str | Path) -> str:
        """
        Preprocess audio for Parakeet model requirements.

        Args:
            audio_path: Path to input audio file

        Returns:
            Path to preprocessed audio file
        """
        try:
            # Load audio with librosa
            audio, original_sr = librosa.load(str(audio_path), sr=None)

            # Target sample rate for Parakeet models (16kHz is optimal)
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
            temp_dir = Path(tempfile.gettempdir()) / "parakeet_preprocessed"
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
        Clean and normalize transcription text using EXACT same method as EpisodeMatcher.

        This ensures compatibility with the existing matching algorithm.

        Args:
            text: Raw transcription text

        Returns:
            Cleaned text using identical cleaning as EpisodeMatcher.clean_text()
        """
        if not text:
            return ""

        # Use EXACT same cleaning logic as EpisodeMatcher.clean_text()
        text = text.lower().strip()
        text = re.sub(r"\[.*?\]|\<.*?\>", "", text)
        text = re.sub(r"([A-Za-z])-\1+", r"\1", text)
        return " ".join(text.split())

    def calculate_match_score(self, transcription: str, reference: str) -> float:
        """
        Calculate similarity score with Parakeet-specific weights.
        Parakeet produces longer, more detailed transcriptions, so we favor partial matches.
        """
        # Parakeet weights: Boost partial_ratio
        token_weight = 0.4
        partial_weight = 0.6

        # Additional boost for very detailed transcriptions
        length_ratio = len(transcription) / max(len(reference), 1)
        if length_ratio > 2.0:  # Much longer transcription
            partial_weight = 0.8
            token_weight = 0.2

        score = (
            fuzz.token_sort_ratio(transcription, reference) * token_weight
            + fuzz.partial_ratio(transcription, reference) * partial_weight
        ) / 100.0

        return score

    def transcribe(self, audio_path: str | Path) -> dict:
        """
        Transcribe audio using Parakeet with preprocessing and text normalization.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with 'text' and 'segments' from Parakeet
        """
        if not self.is_loaded:
            self.load()

        preprocessed_audio = None
        try:
            logger.debug(f"Starting Parakeet transcription for {audio_path}")

            # Preprocess audio for optimal Parakeet performance
            preprocessed_audio = self._preprocess_audio(audio_path)

            # Configure NeMo model settings to reduce warnings
            old_env_vars = {}
            try:
                # Set environment variables to reduce NeMo warnings
                env_settings = {
                    "CUDA_LAUNCH_BLOCKING": "0",
                    "NEMO_DISABLE_TRAINING_LOGS": "1",
                }

                for key, value in env_settings.items():
                    old_env_vars[key] = os.environ.get(key)
                    os.environ[key] = value

                # Parakeet expects list of file paths
                result = self._model.transcribe([preprocessed_audio])

            finally:
                # Restore original environment variables
                for key, old_value in old_env_vars.items():
                    if old_value is not None:
                        os.environ[key] = old_value
                    elif key in os.environ:
                        del os.environ[key]

            logger.debug(f"Parakeet raw result: {result}, type: {type(result)}")

            # Extract text from result
            raw_text = ""
            if isinstance(result, list) and len(result) > 0:
                if hasattr(result[0], "text"):
                    raw_text = result[0].text
                elif isinstance(result[0], str):
                    raw_text = result[0]
                else:
                    raw_text = str(result[0])
            else:
                logger.warning(f"Unexpected Parakeet result format: {result}")
                raw_text = ""

            # Clean and normalize the transcription
            cleaned_text = self._clean_transcription_text(raw_text)

            logger.debug(f"Raw transcription: '{raw_text}'")
            logger.debug(f"Cleaned transcription: '{cleaned_text}'")

            return {
                "text": cleaned_text,
                "raw_text": raw_text,
                "segments": [],
                "language": "en",
            }

        except Exception as e:
            logger.error(
                f"Parakeet transcription failed for {audio_path}: {type(e).__name__}: {e}"
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


class ParakeetCTCModel(ParakeetTDTModel):
    """
    NVIDIA Parakeet CTC ASR model implementation.

    This uses the CTC decoder which is more stable and robust on various hardware
    than the TDT version, though potentially slightly less accurate.
    """

    def __init__(
        self, model_name: str = "nvidia/parakeet-ctc-0.6b", device: str | None = None
    ):
        """
        Initialize Parakeet CTC model.

        Args:
            model_name: Parakeet model identifier (default: nvidia/parakeet-ctc-0.6b)
            device: Device to run on
        """
        # Ensure we use a CTC-compatible model name if not specified
        # But we trust the user input if provided.
        super().__init__(model_name, device)

    def load(self):
        """Load Parakeet CTC model with caching."""
        # We override load simply to use a different cache key if needed, or we can just reuse parent load
        # reusing parent load is fine as it uses self.model_name in cache key.
        # But we need to ensure the logging says CTC.
        super().load()


def create_asr_model(model_config: dict) -> ASRModel:
    """
    Factory function to create ASR models from configuration.

    Args:
        model_config: Dictionary with 'type' and 'name' keys

    Returns:
        Configured ASRModel instance

    Example:
        model_config = {"type": "parakeet", "name": "nvidia/parakeet-ctc-0.6b"}
        model = create_asr_model(model_config)
    """
    model_type = model_config.get("type", "").lower()
    model_name = model_config.get("name", "")
    device = model_config.get("device")

    if model_type == "parakeet":
        # Always use the specific working model
        if not model_name:
            model_name = "nvidia/parakeet-ctc-0.6b"
        return ParakeetCTCModel(model_name, device)
    else:
        raise ValueError(
            f"Unsupported model type: {model_type}. Only 'parakeet' is supported."
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

    # Check Parakeet availability
    try:
        import nemo.collections.asr  # noqa: F401

        availability["parakeet"] = {
            "available": True,
            "models": ["nvidia/parakeet-ctc-0.6b"],
        }
    except ImportError:
        availability["parakeet"] = {
            "available": False,
            "error": "NVIDIA NeMo not installed",
        }

    return availability
