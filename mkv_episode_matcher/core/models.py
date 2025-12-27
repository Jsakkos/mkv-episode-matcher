from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EpisodeInfo(BaseModel):
    """Data model for episode information."""

    series_name: str
    season: int
    episode: int
    title: str | None = None

    @property
    def s_e_format(self) -> str:
        return f"S{self.season:02d}E{self.episode:02d}"


class SubtitleFile(BaseModel):
    """Data model for a subtitle file."""

    path: Path
    language: str = "en"
    episode_info: EpisodeInfo | None = None
    content: str | None = None  # Loaded content (optional)


class AudioChunk(BaseModel):
    """Data model for an extracted audio chunk."""

    path: Path
    start_time: float
    duration: float


class MatchResult(BaseModel):
    """Data model for a matching result."""

    episode_info: EpisodeInfo
    confidence: float
    matched_file: Path
    matched_time: float
    chunk_index: int = 0
    model_name: str
    original_file: Path | None = None  # Store original filename for display


class FailedMatch(BaseModel):
    """Data model for a failed match."""

    original_file: Path
    reason: str
    confidence: float = 0.0
    series_name: str | None = None
    season: int | None = None


class MatchCandidate(BaseModel):
    """A candidate match from a single chunk."""

    episode_info: EpisodeInfo
    confidence: float
    reference_file: Path


class Config(BaseModel):
    """Global configuration model."""

    tmdb_api_key: str | None = None
    show_dir: Path | None = None
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mkv-episode-matcher" / "cache"
    )
    min_confidence: float = 0.7

    # OpenSubtitles settings
    open_subtitles_api_key: str | None = None
    open_subtitles_username: str | None = None
    open_subtitles_password: str | None = None
    open_subtitles_user_agent: str = "Oz 1.0.0"

    # Provider settings
    asr_provider: Literal["parakeet"] = "parakeet"
    sub_provider: Literal["opensubtitles", "local"] = "opensubtitles"

    @field_validator("show_dir")
    def validate_show_dir(cls, v):
        if v and not v.exists():
            raise ValueError(f"Show directory does not exist: {v}")
        return v
