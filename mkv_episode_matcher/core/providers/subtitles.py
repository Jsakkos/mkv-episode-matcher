import abc
import re
import shutil
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from loguru import logger
from opensubtitlescom import OpenSubtitles

F = TypeVar("F", bound=Callable[..., Any])

from mkv_episode_matcher.core.config_manager import get_config_manager
from mkv_episode_matcher.core.models import EpisodeInfo, SubtitleFile


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
) -> Callable[[F], F]:
    """Decorator for retrying operations with exponential backoff."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise e

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}, retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exception

        return wrapper  # type: ignore

    return decorator


def parse_season_episode(filename: str) -> EpisodeInfo | None:
    """Parse season and episode from filename using regex."""
    # S01E01
    match = re.search(r"[Ss](\d{1,2})[Ee](\d{1,2})", filename)
    if match:
        return EpisodeInfo(
            series_name="",  # Placeholder
            season=int(match.group(1)),
            episode=int(match.group(2)),
        )
    # 1x01
    match = re.search(r"(\d{1,2})x(\d{1,2})", filename)
    if match:
        return EpisodeInfo(
            series_name="", season=int(match.group(1)), episode=int(match.group(2))
        )
    return None


class SubtitleProvider(abc.ABC):
    @abc.abstractmethod
    def get_subtitles(
        self, show_name: str, season: int, video_files: list[Path] = None
    ) -> list[SubtitleFile]:
        pass


class LocalSubtitleProvider(SubtitleProvider):
    """Provider that scans a local directory for subtitle files."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / "data"

    def get_subtitles(
        self, show_name: str, season: int, video_files: list[Path] = None
    ) -> list[SubtitleFile]:
        """Get all subtitle files for a specific show and season."""
        show_dir = self.cache_dir / show_name
        if not show_dir.exists():
            # logger.warning(f"No subtitle cache found at {show_dir}")
            return []

        subtitles = []
        # Case insensitive glob
        files = list(show_dir.glob("*.srt")) + list(show_dir.glob("*.SRT"))

        for f in files:
            info = parse_season_episode(f.name)
            if info:
                if info.season == season:
                    info.series_name = show_name
                    subtitles.append(SubtitleFile(path=f, episode_info=info))

        # Deduplicate by path
        seen = set()
        unique_subs = []
        for sub in subtitles:
            if sub.path not in seen:
                seen.add(sub.path)
                unique_subs.append(sub)

        return unique_subs


class OpenSubtitlesProvider(SubtitleProvider):
    """Provider that downloads subtitles using OpenSubtitles.com."""

    def __init__(self):
        cm = get_config_manager()
        self.config = cm.load()
        self.client = None
        self.network_timeout = 30  # seconds
        self._authenticate()

    def _authenticate(self):
        if not self.config.open_subtitles_api_key:
            logger.warning("OpenSubtitles API key not configured")
            return

        try:
            self.client = OpenSubtitles(
                self.config.open_subtitles_user_agent,
                self.config.open_subtitles_api_key,
            )
            if (
                self.config.open_subtitles_username
                and self.config.open_subtitles_password
            ):
                self.client.login(
                    self.config.open_subtitles_username,
                    self.config.open_subtitles_password,
                )
                logger.debug("Logged in to OpenSubtitles")
            else:
                logger.debug("Initialized OpenSubtitles (no login)")
        except Exception as e:
            logger.error(f"Failed to initialize OpenSubtitles: {e}")
            self.client = None

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def _search_with_retry(self, query: str, languages: str = "en"):
        """Search for subtitles with retry logic."""
        if not self.client:
            raise RuntimeError("OpenSubtitles client not initialized")

        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(
                f"Search operation timed out after {self.network_timeout}s"
            )

        # Set timeout for search operation (Unix-like systems only)
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.network_timeout)

        try:
            return self.client.search(query=query, languages=languages)
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)  # Cancel the alarm

    @retry_with_backoff(max_retries=2, base_delay=0.5)
    def _download_with_retry(self, subtitle):
        """Download subtitle file with retry logic."""
        if not self.client:
            raise RuntimeError("OpenSubtitles client not initialized")

        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(
                f"Download operation timed out after {self.network_timeout}s"
            )

        # Set timeout for download operation (Unix-like systems only)
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.network_timeout)

        try:
            return self.client.download_and_save(subtitle)
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)  # Cancel the alarm

    def get_subtitles(
        self, show_name: str, season: int, video_files: list[Path] = None
    ) -> list[SubtitleFile]:
        """Get subtitles for a show/season by downloading them."""
        if not self.client:
            logger.error("OpenSubtitles client not available")
            return []

        # We need video files to do specific searching usually, but if we just want to bulk match
        # we might want to search by query.
        # However, the engine usually passes a list of video files for the season.

        # If we have video files, we can try to find subs for them specifically?
        # Or just search for "Show Name S01" to get a bunch?
        # OpenSubtitles API allows searching by query "Show Name S01".

        logger.info(f"Searching OpenSubtitles for {show_name} S{season:02d}")

        # Prepare cache directory
        cache_dir = self.config.cache_dir / "data" / show_name
        cache_dir.mkdir(parents=True, exist_ok=True)

        downloaded_subtitles = []

        try:
            # Search by query with retry logic
            query = f"{show_name} S{season:02d}"
            response = self._search_with_retry(query)

            if not response.data:
                logger.warning(f"No subtitles found for query: {query}")
                return []

            logger.info(f"Found {len(response.data)} potential subtitles")

            # Limit downloads to a reasonable number or try to match specifically?
            # For now, let's download unique episodes for this season.

            seen_episodes = set()

            for subtitle in response.data:
                # Use API provided metadata first
                api_season = getattr(subtitle, "season_number", None)
                api_episode = getattr(subtitle, "episode_number", None)

                # Get filename from files list or top level
                sub_filename = subtitle.file_name
                if not sub_filename and subtitle.files:
                    # files is a list of dicts based on debug output
                    if isinstance(subtitle.files[0], dict):
                        sub_filename = subtitle.files[0].get("file_name", "")
                    else:
                        # Fallback if it somehow changes to object
                        sub_filename = getattr(subtitle.files[0], "file_name", "")

                # Check match
                if api_season and api_episode:
                    if api_season != season:
                        continue
                    ep_num = api_episode
                else:
                    # Fallback to parsing filename
                    info = parse_season_episode(sub_filename or "")
                    if not info or info.season != season:
                        continue
                    ep_num = info.episode

                if ep_num in seen_episodes:
                    continue

                # Download with retry
                try:
                    logger.info(f"Downloading subtitle for S{season:02d}E{ep_num:02d}")
                    srt_file = self._download_with_retry(subtitle)

                    # Move to cache
                    target_name = f"{show_name} - S{season:02d}E{ep_num:02d}.srt"
                    target_path = cache_dir / target_name

                    shutil.move(srt_file, target_path)

                    downloaded_subtitles.append(
                        SubtitleFile(
                            path=target_path,
                            language="en",
                            episode_info=EpisodeInfo(
                                series_name=show_name, season=season, episode=ep_num
                            ),
                        )
                    )
                    seen_episodes.add(ep_num)

                except Exception as e:
                    logger.error(f"Failed to download/save subtitle: {e}")

            return downloaded_subtitles

        except Exception as e:
            logger.error(f"OpenSubtitles search failed: {e}")
            return []


class CompositeSubtitleProvider(SubtitleProvider):
    def __init__(self, providers: list[SubtitleProvider]):
        self.providers = providers

    def get_subtitles(
        self, show_name: str, season: int, video_files: list[Path] = None
    ) -> list[SubtitleFile]:
        results = []

        # Try each provider in order, but prioritize cached results
        for i, provider in enumerate(self.providers):
            provider_results = provider.get_subtitles(show_name, season, video_files)

            # If this is the local provider and we have results, prefer them
            if isinstance(provider, LocalSubtitleProvider) and provider_results:
                logger.info(
                    f"Found {len(provider_results)} cached subtitles for {show_name} S{season:02d}"
                )
                results.extend(provider_results)
                # Return early if we have enough cached subtitles
                if (
                    len(provider_results) >= 3
                ):  # Arbitrary threshold for "enough" episodes
                    logger.info("Using cached subtitles, skipping download")
                    return results
            else:
                # For non-local providers, only use if we don't have cached results
                if not results:
                    logger.info(f"No cached subtitles found, trying provider {i + 1}")
                    results.extend(provider_results)
                else:
                    logger.info(
                        "Skipping additional providers since cached subtitles are available"
                    )
                    break

        return results
