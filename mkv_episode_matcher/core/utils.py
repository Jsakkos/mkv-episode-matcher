import re
from pathlib import Path

import chardet
from loguru import logger


def detect_file_encoding(file_path: Path) -> str:
    """Detect the encoding of a file using chardet."""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(min(1024 * 1024, file_path.stat().st_size))
        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        return encoding if encoding else "utf-8"
    except Exception as e:
        logger.warning(f"Error detecting encoding for {file_path}: {e}")
        return "utf-8"


def read_file_with_fallback(file_path: Path, encodings: list[str] | None = None) -> str:
    """Read a file trying multiple encodings."""
    if encodings is None:
        detected = detect_file_encoding(file_path)
        encodings = [detected, "utf-8", "latin-1", "cp1252", "iso-8859-1"]

    errors = []
    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as e:
            errors.append(f"{encoding}: {str(e)}")
            continue

    raise ValueError(f"Failed to read {file_path} with any encoding. Errors: {errors}")


class SubtitleReader:
    """Helper class for reading and parsing subtitle files."""

    @staticmethod
    def parse_timestamp(timestamp: str) -> float:
        """Parse SRT timestamp into seconds."""
        hours, minutes, seconds = timestamp.replace(",", ".").split(":")
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

    @staticmethod
    def read_srt_file(file_path: Path) -> str:
        return read_file_with_fallback(file_path)

    @staticmethod
    def extract_subtitle_chunk(
        content: str, start_time: float, end_time: float
    ) -> list[str]:
        """Extract subtitle text for a specific time window."""
        text_lines = []
        for block in content.strip().split("\n\n"):
            lines = block.split("\n")
            if len(lines) < 3 or "-->" not in lines[1]:
                continue
            try:
                timestamp = lines[1]
                time_parts = timestamp.split(" --> ")
                s_stamp = SubtitleReader.parse_timestamp(time_parts[0].strip())
                e_stamp = SubtitleReader.parse_timestamp(time_parts[1].strip())

                if e_stamp >= start_time and s_stamp <= end_time:
                    text_lines.append(" ".join(lines[2:]))
            except (IndexError, ValueError):
                continue
        return text_lines


def clean_text(text: str) -> str:
    """Clean and normalize text for matching."""
    text = text.lower().strip()
    text = re.sub(r"\[.*?\]|\<.*?\>", "", text)
    text = re.sub(r"([A-Za-z])-\1+", r"\1", text)
    return " ".join(text.split())


import subprocess


def get_video_duration(video_file: Path) -> float:
    """Get video duration using ffprobe."""
    try:
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
            raise RuntimeError(f"ffprobe error: {result.stderr}")

        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to get duration for {video_file}: {e}")
        return 0.0


def extract_audio_chunk(
    video_file: Path, start_time: float, duration: float, output_path: Path
) -> Path:
    """Extract audio chunk using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-ss",
        str(start_time),
        "-t",
        str(duration),
        "-i",
        str(video_file),
        "-vn",
        "-sn",
        "-dn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=30)
        if not output_path.exists() or output_path.stat().st_size < 1024:
            raise RuntimeError("Output file too small or missing")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise
