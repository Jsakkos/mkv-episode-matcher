from pathlib import Path
from typing import Literal
import os
import json

from pydantic import BaseModel, Field, field_validator, model_validator


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
    asr_provider: Literal["whisper", "parakeet"] = "whisper"  # parakeet kept for migration
    asr_model_name: str = "small"
    sub_provider: Literal["opensubtitles", "local"] = "opensubtitles"

    @model_validator(mode="before")
    @classmethod
    def migrate_asr_provider(cls, data: dict) -> dict:
        """Migrate legacy parakeet config to whisper."""
        if isinstance(data, dict):
            # Migrate parakeet to whisper
            if data.get("asr_provider") == "parakeet":
                data["asr_provider"] = "whisper"
                data["asr_model_name"] = "small"  # Default whisper model
        return data

    @field_validator("show_dir")
    def validate_show_dir(cls, v):
        if v and not v.exists():
            raise ValueError(f"Show directory does not exist: {v}")
        return v


class ConfigManager:
    """Manages configuration loading and saving."""
    
    def __init__(self, config_path: Path | None = None):
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = Path.home() / ".mkv-episode-matcher" / "config.json"
        
        self.config = self._load_config()

    def _load_config(self) -> Config:
        """Load config from file or environment variables."""
        config_data = {}
        
        # Load from file if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config_data = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")

        # Override with environment variables
        if os.getenv("TMDB_API_KEY"):
            config_data["tmdb_api_key"] = os.getenv("TMDB_API_KEY")
            
        # Create Config object
        return Config(**config_data)

    def save_config(self):
        """Save current config to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            f.write(self.config.model_dump_json(indent=2))
