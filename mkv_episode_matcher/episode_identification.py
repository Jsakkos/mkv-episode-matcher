import re
import subprocess
import tempfile
from pathlib import Path
from rich import print
from rich.console import Console
import chardet
import numpy as np
import torch
import whisper
from loguru import logger
from rapidfuzz import fuzz

console = Console()

class EpisodeMatcher:
    def __init__(self, cache_dir, show_name, min_confidence=0.6):
        self.cache_dir = Path(cache_dir)
        self.min_confidence = min_confidence
        self.show_name = show_name
        self.chunk_duration = 30
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.temp_dir = Path(tempfile.gettempdir()) / "whisper_chunks"
        self.temp_dir.mkdir(exist_ok=True)

    def clean_text(self, text):
        text = text.lower().strip()
        text = re.sub(r"\[.*?\]|\<.*?\>", "", text)
        text = re.sub(r"([A-Za-z])-\1+", r"\1", text)
        return " ".join(text.split())

    def chunk_score(self, whisper_chunk, ref_chunk):
        whisper_clean = self.clean_text(whisper_chunk)
        ref_clean = self.clean_text(ref_chunk)
        return (
            fuzz.token_sort_ratio(whisper_clean, ref_clean) * 0.7
            + fuzz.partial_ratio(whisper_clean, ref_clean) * 0.3
        ) / 100.0

    def extract_audio_chunk(self, mkv_file, start_time):
        """Extract a chunk of audio from MKV file."""
        chunk_path = self.temp_dir / f"chunk_{start_time}.wav"
        if not chunk_path.exists():
            cmd = [
                "ffmpeg",
                "-ss",
                str(start_time),
                "-t",
                str(self.chunk_duration),
                "-i",
                mkv_file,
                "-vn",  # Disable video
                "-sn",  # Disable subtitles
                "-dn",  # Disable data streams
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(chunk_path),
            ]
            subprocess.run(cmd, capture_output=True)
        return str(chunk_path)

    def load_reference_chunk(self, srt_file, chunk_idx):
        """
        Load reference subtitles for a specific time chunk with robust encoding handling.

        Args:
            srt_file (str or Path): Path to the SRT file
            chunk_idx (int): Index of the chunk to load

        Returns:
            str: Combined text from the subtitle chunk
        """
        chunk_start = chunk_idx * self.chunk_duration
        chunk_end = chunk_start + self.chunk_duration

        try:
            # Read the file content using our robust reader
            reader = SubtitleReader()
            content = reader.read_srt_file(srt_file)

            # Extract subtitles for the time chunk
            text_lines = reader.extract_subtitle_chunk(content, chunk_start, chunk_end)

            return " ".join(text_lines)

        except Exception as e:
            logger.error(f"Error loading reference chunk from {srt_file}: {e}")
            return ""

    def _try_match_with_model(
        self, video_file, model_name, max_duration, reference_files
    ):
        """
        Attempt to match using specified model, checking multiple 30-second chunks up to max_duration.

        Args:
            video_file: Path to the video file
            model_name: Name of the Whisper model to use
            max_duration: Maximum duration in seconds to check
            reference_files: List of reference subtitle files
        """
        # Use cached model
        model = get_whisper_model(model_name, self.device)

        # Calculate number of chunks to check (30 seconds each)
        num_chunks = max_duration // self.chunk_duration

        for chunk_idx in range(num_chunks):
            start_time = chunk_idx * self.chunk_duration
            logger.debug(f"Trying {model_name} model at {start_time} seconds")

            audio_path = self.extract_audio_chunk(video_file, start_time)

            result = model.transcribe(audio_path, task="transcribe", language="en")

            chunk_text = result["text"]
            best_confidence = 0
            best_match = None

            # Compare with reference chunks
            for ref_file in reference_files:
                ref_text = self.load_reference_chunk(ref_file, chunk_idx)
                confidence = self.chunk_score(chunk_text, ref_text)

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = ref_file

                if confidence > self.min_confidence:
                    season_ep = re.search(r"S(\d+)E(\d+)", best_match.stem)
                    if season_ep:
                        season, episode = map(int, season_ep.groups())
                        return {
                            "season": season,
                            "episode": episode,
                            "confidence": best_confidence,
                            "reference_file": str(best_match),
                            "matched_at": start_time,
                        }

            logger.info(
                f"No match found at {start_time} seconds (best confidence: {best_confidence:.2f})"
            )
        return None

    def identify_episode(self, video_file, temp_dir, season_number):
        """Progressive episode identification with faster initial attempt."""
        try:
            # Get reference files first
            reference_dir = self.cache_dir / "data" / self.show_name
            patterns = [
                f"S{season_number:02d}E",
                f"S{season_number}E",
                f"{season_number:02d}x",
                f"{season_number}x",
            ]

            reference_files = []
            # TODO Figure our why patterns is not being used
            for _pattern in patterns:
                files = [
                    f
                    for f in reference_dir.glob("*.srt")
                    if any(
                        re.search(f"{p}\\d+", f.name, re.IGNORECASE) for p in patterns
                    )
                ]
                reference_files.extend(files)

            reference_files = list(dict.fromkeys(reference_files))

            if not reference_files:
                logger.error(f"No reference files found for season {season_number}")
                return None
            duration = float(
                subprocess.check_output([
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    video_file,
                ]).decode()
            )

            duration = int(np.ceil(duration))
            # Try with tiny model first (fastest)
            logger.info("Attempting match with tiny model...")
            match = self._try_match_with_model(
                video_file, "tiny", duration, reference_files
            )
            if (
                match and match["confidence"] > 0.65
            ):  # Slightly lower threshold for tiny
                logger.info(
                    f"Successfully matched with tiny model at {match['matched_at']}s (confidence: {match['confidence']:.2f})"
                )
                return match

            # If no match, try base model
            logger.info(
                "No match in first 3 minutes, extending base model search to 10 minutes..."
            )
            match = self._try_match_with_model(
                video_file, "base", duration, reference_files
            )
            if match:
                logger.info(
                    f"Successfully matched with base model at {match['matched_at']}s (confidence: {match['confidence']:.2f})"
                )
                return match

            logger.info("Speech recognition match failed")
            return None

        finally:
            # Cleanup temp files
            for file in self.temp_dir.glob("chunk_*.wav"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {file}: {e}")


def detect_file_encoding(file_path):
    """
    Detect the encoding of a file using chardet.

    Args:
        file_path (str or Path): Path to the file

    Returns:
        str: Detected encoding, defaults to 'utf-8' if detection fails
    """
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        confidence = result["confidence"]

        logger.debug(
            f"Detected encoding {encoding} with {confidence:.2%} confidence for {file_path}"
        )
        return encoding if encoding else "utf-8"
    except Exception as e:
        logger.warning(f"Error detecting encoding for {file_path}: {e}")
        return "utf-8"


def read_file_with_fallback(file_path, encodings=None):
    """
    Read a file trying multiple encodings in order of preference.

    Args:
        file_path (str or Path): Path to the file
        encodings (list): List of encodings to try, defaults to common subtitle encodings

    Returns:
        str: File contents

    Raises:
        ValueError: If file cannot be read with any encoding
    """
    if encodings is None:
        # First try detected encoding, then fallback to common subtitle encodings
        detected = detect_file_encoding(file_path)
        encodings = [detected, "utf-8", "latin-1", "cp1252", "iso-8859-1"]

    file_path = Path(file_path)
    errors = []

    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {file_path} using {encoding} encoding")
            return content
        except UnicodeDecodeError as e:
            errors.append(f"{encoding}: {str(e)}")
            continue

    error_msg = f"Failed to read {file_path} with any encoding. Errors:\n" + "\n".join(
        errors
    )
    logger.error(error_msg)
    raise ValueError(error_msg)


class SubtitleReader:
    """Helper class for reading and parsing subtitle files."""

    @staticmethod
    def parse_timestamp(timestamp):
        """Parse SRT timestamp into seconds."""
        hours, minutes, seconds = timestamp.replace(",", ".").split(":")
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    @staticmethod
    def read_srt_file(file_path):
        """
        Read an SRT file and return its contents with robust encoding handling.

        Args:
            file_path (str or Path): Path to the SRT file

        Returns:
            str: Contents of the SRT file
        """
        return read_file_with_fallback(file_path)

    @staticmethod
    def extract_subtitle_chunk(content, start_time, end_time):
        """
        Extract subtitle text for a specific time window.

        Args:
            content (str): Full SRT file content
            start_time (float): Chunk start time in seconds
            end_time (float): Chunk end time in seconds

        Returns:
            list: List of subtitle texts within the time window
        """
        text_lines = []

        for block in content.strip().split("\n\n"):
            lines = block.split("\n")
            if len(lines) < 3 or "-->" not in lines[1]:
                continue

            try:
                timestamp = lines[1]
                text = " ".join(lines[2:])

                end_stamp = timestamp.split(" --> ")[1].strip()
                total_seconds = SubtitleReader.parse_timestamp(end_stamp)

                if start_time <= total_seconds <= end_time:
                    text_lines.append(text)

            except (IndexError, ValueError) as e:
                logger.warning(f"Error parsing subtitle block: {e}")
                continue

        return text_lines


_whisper_models = {}


def get_whisper_model(model_name="tiny", device=None):
    """Cache whisper models to avoid reloading."""
    global _whisper_models
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    key = f"{model_name}_{device}"
    if key not in _whisper_models:
        _whisper_models[key] = whisper.load_model(model_name, device=device)
        logger.info(f"Loaded {model_name} model on {device}")

    return _whisper_models[key]
