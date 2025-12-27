import re
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import chardet
import numpy as np
import torch
from loguru import logger
from rich import print
from rich.console import Console

from mkv_episode_matcher.asr_models import get_cached_model
from mkv_episode_matcher.utils import extract_season_episode

console = Console()


class SubtitleCache:
    """Cache for storing parsed subtitle data to avoid repeated loading and parsing."""

    def __init__(self):
        self.subtitles = {}  # {file_path: parsed_content}
        self.chunk_cache = {}  # {(file_path, chunk_idx): text}

    def get_subtitle_content(self, srt_file):
        """Get the full content of a subtitle file, loading it only once."""
        srt_file = str(srt_file)
        if srt_file not in self.subtitles:
            reader = SubtitleReader()
            self.subtitles[srt_file] = reader.read_srt_file(srt_file)
        return self.subtitles[srt_file]

    def get_chunk(self, srt_file, chunk_idx, chunk_start, chunk_end):
        """Get a specific time chunk from a subtitle file, with caching."""
        srt_file = str(srt_file)
        cache_key = (srt_file, chunk_idx)

        if cache_key not in self.chunk_cache:
            content = self.get_subtitle_content(srt_file)
            reader = SubtitleReader()
            text_lines = reader.extract_subtitle_chunk(content, chunk_start, chunk_end)
            self.chunk_cache[cache_key] = " ".join(text_lines)

        return self.chunk_cache[cache_key]


class EpisodeMatcher:
    def __init__(self, cache_dir, show_name, min_confidence=0.6, device=None):
        self.cache_dir = Path(cache_dir)
        self.min_confidence = min_confidence
        self.show_name = show_name
        self.chunk_duration = 30
        self.skip_initial_duration = 300
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.temp_dir = Path(tempfile.gettempdir()) / "whisper_chunks"
        self.temp_dir.mkdir(exist_ok=True)
        # Initialize subtitle cache
        self.subtitle_cache = SubtitleCache()
        # Cache for extracted audio chunks
        self.audio_chunks = {}
        # Store reference files to avoid repeated glob operations
        self.reference_files_cache = {}

    def clean_text(self, text):
        text = text.lower().strip()
        text = re.sub(r"\[.*?\]|\<.*?\>", "", text)
        text = re.sub(r"([A-Za-z])-\1+", r"\1", text)
        return " ".join(text.split())

    def extract_audio_chunk(self, mkv_file, start_time):
        """Extract a chunk of audio from MKV file with caching."""
        cache_key = (str(mkv_file), start_time)

        if cache_key in self.audio_chunks:
            return self.audio_chunks[cache_key]

        chunk_path = self.temp_dir / f"chunk_{start_time}.wav"
        if not chunk_path.exists():
            cmd = [
                "ffmpeg",
                "-ss",
                str(start_time),
                "-t",
                str(self.chunk_duration),
                "-i",
                str(mkv_file),
                "-vn",  # Disable video
                "-sn",  # Disable subtitles
                "-dn",  # Disable data streams
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-y",  # Overwrite output files without asking
                str(chunk_path),
            ]

            try:
                logger.debug(
                    f"Extracting audio chunk from {mkv_file} at {start_time}s using FFmpeg"
                )
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    error_msg = f"FFmpeg failed with return code {result.returncode}"
                    if result.stderr:
                        error_msg += f". Error: {result.stderr.strip()}"
                    logger.error(error_msg)
                    logger.debug(f"FFmpeg command: {' '.join(cmd)}")
                    raise RuntimeError(error_msg)

                # Check if the output file was actually created and has content
                if not chunk_path.exists():
                    error_msg = f"FFmpeg completed but output file was not created: {chunk_path}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

                # Check if the file has meaningful content (at least 1KB)
                if chunk_path.stat().st_size < 1024:
                    error_msg = f"Generated audio chunk is too small ({chunk_path.stat().st_size} bytes), likely corrupted"
                    logger.warning(error_msg)
                    # Don't raise an error for small files, but log the warning

                logger.debug(
                    f"Successfully extracted {chunk_path.stat().st_size} byte audio chunk"
                )

            except subprocess.TimeoutExpired as e:
                error_msg = f"FFmpeg timed out after 30 seconds while extracting audio from {mkv_file}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

            except Exception as e:
                error_msg = f"Failed to extract audio chunk from {mkv_file} at {start_time}s: {str(e)}"
                logger.error(error_msg)
                # Clean up partial file if it exists
                if chunk_path.exists():
                    try:
                        chunk_path.unlink()
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Failed to clean up partial file {chunk_path}: {cleanup_error}"
                        )
                raise RuntimeError(error_msg) from e

        chunk_path_str = str(chunk_path)
        self.audio_chunks[cache_key] = chunk_path_str
        return chunk_path_str

    def load_reference_chunk(self, srt_file, chunk_idx):
        """
        Load reference subtitles for a specific time chunk with caching.

        Args:
            srt_file (str or Path): Path to the SRT file
            chunk_idx (int): Index of the chunk to load

        Returns:
            str: Combined text from the subtitle chunk
        """
        try:
            # Apply the same offset as in _try_match_with_model
            chunk_start = self.skip_initial_duration + (chunk_idx * self.chunk_duration)
            chunk_end = chunk_start + self.chunk_duration

            return self.subtitle_cache.get_chunk(
                srt_file, chunk_idx, chunk_start, chunk_end
            )

        except Exception as e:
            logger.error(f"Error loading reference chunk from {srt_file}: {e}")
            return ""

    def get_reference_files(self, season_number):
        """Get reference subtitle files with caching."""
        cache_key = (self.show_name, season_number)
        logger.debug(f"Reference cache key: {cache_key}")

        if cache_key in self.reference_files_cache:
            logger.debug("Returning cached reference files")
            return self.reference_files_cache[cache_key]

        reference_dir = self.cache_dir / "data" / self.show_name
        patterns = [
            f"S{season_number:02d}E",
            f"S{season_number}E",
            f"{season_number:02d}x",
            f"{season_number}x",
        ]

        reference_files = []
        for pattern in patterns:
            # Use case-insensitive file extension matching by checking both .srt and .SRT
            srt_files = list(reference_dir.glob("*.srt")) + list(
                reference_dir.glob("*.SRT")
            )
            files = [
                f
                for f in srt_files
                if re.search(f"{pattern}\\d+", f.name, re.IGNORECASE)
            ]
            reference_files.extend(files)

        # Remove duplicates while preserving order
        reference_files = list(dict.fromkeys(reference_files))
        logger.debug(
            f"Found {len(reference_files)} reference files for season {season_number}"
        )
        self.reference_files_cache[cache_key] = reference_files
        return reference_files

    def _try_match_with_model(
        self, video_file, model_config, max_duration, reference_files
    ):
        """
        Attempt to match using specified model, checking multiple chunks starting from skip_initial_duration
        and continuing up to max_duration.

        Args:
            video_file: Path to the video file
            model_config: Dictionary with ASR model configuration or string for backward compatibility
            max_duration: Maximum duration in seconds to check
            reference_files: List of reference subtitle files
        """
        # Handle backward compatibility for string model names
        if isinstance(model_config, str):
            # Convert old Whisper model names to new format
            model_config = {
                "type": "whisper",
                "name": model_config,
                "device": self.device,
            }
        elif isinstance(model_config, dict):
            # Ensure device is set if not specified
            if "device" not in model_config:
                model_config = model_config.copy()
                model_config["device"] = self.device

        # Use cached model
        model = get_cached_model(model_config)

        # Calculate number of chunks to check
        num_chunks = min(
            max_duration // self.chunk_duration, 10
        )  # Limit to 10 chunks for initial check

        # Pre-load all reference chunks for the chunks we'll check
        for chunk_idx in range(num_chunks):
            for ref_file in reference_files:
                self.load_reference_chunk(ref_file, chunk_idx)

        for chunk_idx in range(num_chunks):
            # Start at self.skip_initial_duration and check subsequent chunks
            start_time = self.skip_initial_duration + (chunk_idx * self.chunk_duration)
            model_name = (
                model_config.get("name", "unknown")
                if isinstance(model_config, dict)
                else model_config
            )
            logger.debug(f"Trying {model_name} model at {start_time} seconds")

            try:
                audio_path = self.extract_audio_chunk(video_file, start_time)
                logger.debug(f"Extracted audio chunk: {audio_path}")
            except RuntimeError as e:
                logger.warning(f"Failed to extract audio chunk at {start_time}s: {e}")
                continue  # Skip this chunk and try the next one
            except Exception as e:
                logger.error(
                    f"Unexpected error extracting audio chunk at {start_time}s: {e}"
                )
                continue  # Skip this chunk and try the next one

            try:
                result = model.transcribe(audio_path)
            except Exception as e:
                logger.error(
                    f"ASR transcription failed for chunk at {start_time}s: {e}"
                )
                continue  # Skip this chunk and try the next one

            chunk_text = result["text"]
            logger.debug(
                f"Transcription result: {chunk_text} ({len(chunk_text)} characters)"
            )
            if len(chunk_text) < 10:
                logger.debug(
                    f"Transcription result too short: {chunk_text} ({len(chunk_text)} characters)"
                )
                continue
            best_confidence = 0
            best_match = None

            # Compare with reference chunks
            # Compare with reference chunks
            for ref_file in reference_files:
                ref_text = self.load_reference_chunk(ref_file, chunk_idx)

                # Use model's internal scoring logic
                confidence = model.calculate_match_score(chunk_text, ref_text)

                if confidence > best_confidence:
                    logger.debug(f"New best confidence: {confidence} for {ref_file}")
                    best_confidence = confidence
                    best_match = Path(ref_file)

                if confidence > self.min_confidence:
                    print(
                        f"Matched with {best_match} (confidence: {best_confidence:.2f})"
                    )
                    try:
                        season, episode = extract_season_episode(best_match.stem)
                    except Exception as e:
                        print(f"Error extracting season/episode: {e}")
                        continue
                    print(
                        f"Season: {season}, Episode: {episode} (confidence: {best_confidence:.2f})"
                    )
                    if season and episode:
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
            # Get reference files first with caching
            reference_files = self.get_reference_files(season_number)

            if not reference_files:
                logger.error(f"No reference files found for season {season_number}")
                return None

            # Cache video duration
            try:
                duration = get_video_duration(video_file)
            except Exception as e:
                logger.error(f"Failed to get video duration for {video_file}: {e}")
                return None

            # Try with Parakeet CTC model
            logger.info("Attempting match with Parakeet CTC model...")
            try:
                match = self._try_match_with_model(
                    video_file,
                    {
                        "type": "parakeet",
                        "name": "nvidia/parakeet-ctc-0.6b",
                        "device": self.device,
                    },
                    min(duration, 600),  # Allow up to 10 minutes
                    reference_files,
                )
                if match:
                    logger.info(
                        f"Successfully matched with Parakeet CTC model at {match['matched_at']}s (confidence: {match['confidence']:.2f})"
                    )
                    return match
            except Exception as e:
                logger.warning(f"Parakeet CTC model failed: {e}")

            logger.info(
                "Speech recognition match failed - no models were able to process this file"
            )
            return None

        except Exception as e:
            logger.error(
                f"Unexpected error during episode identification for {video_file}: {e}"
            )
            return None

        finally:
            # Cleanup temp files - keep this limited to only files we know we created
            for chunk_info in self.audio_chunks.values():
                try:
                    Path(chunk_info).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {chunk_info}: {e}")


@lru_cache(maxsize=100)
def get_video_duration(video_file):
    """Get video duration with caching and error handling."""
    try:
        logger.debug(f"Getting duration for video file: {video_file}")
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_file),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error_msg = f"ffprobe failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f". Error: {result.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        duration_str = result.stdout.strip()
        if not duration_str:
            raise RuntimeError("ffprobe returned empty duration")

        duration = float(duration_str)
        if duration <= 0:
            raise RuntimeError(f"Invalid duration: {duration}")

        result_duration = int(np.ceil(duration))
        logger.debug(f"Video duration: {result_duration} seconds")
        return result_duration

    except subprocess.TimeoutExpired as e:
        error_msg = f"ffprobe timed out while getting duration for {video_file}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except ValueError as e:
        error_msg = (
            f"Failed to parse duration from ffprobe output for {video_file}: {e}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error getting video duration for {video_file}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


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
            raw_data = f.read(
                min(1024 * 1024, Path(file_path).stat().st_size)
            )  # Read up to 1MB
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


@lru_cache(maxsize=100)
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
                time_parts = timestamp.split(" --> ")
                start_stamp = time_parts[0].strip()
                end_stamp = time_parts[1].strip()

                subtitle_start = SubtitleReader.parse_timestamp(start_stamp)
                subtitle_end = SubtitleReader.parse_timestamp(end_stamp)

                # Check if this subtitle overlaps with our chunk
                if subtitle_end >= start_time and subtitle_start <= end_time:
                    text = " ".join(lines[2:])
                    text_lines.append(text)

            except (IndexError, ValueError) as e:
                logger.warning(f"Error parsing subtitle block: {e}")
                continue

        return text_lines


# Note: Model caching is now handled by the ASR abstraction layer in asr_models.py
