"""
Enhanced MKV Episode Matcher Engine V2

This module provides the core matching engine with:
- Optimized Parakeet ASR singleton
- Enhanced caching system
- Automatic subtitle acquisition
- Progress tracking and rich output
- Multiple use case support
"""

import hashlib
import json
import re
from collections.abc import Generator
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)

from mkv_episode_matcher.core.matcher import MultiSegmentMatcher
from mkv_episode_matcher.core.models import Config, MatchResult
from mkv_episode_matcher.core.providers.asr import get_asr_provider
from mkv_episode_matcher.core.providers.subtitles import (
    CompositeSubtitleProvider,
    LocalSubtitleProvider,
    OpenSubtitlesProvider,
)


class CacheManager:
    """Enhanced caching system with memory bounds and LRU eviction."""

    def __init__(self, cache_dir: Path, max_memory_mb: int = 512, max_items: int = 100):
        self.cache_dir = cache_dir
        self.memory_cache = {}
        self.access_order = {}  # Track access times for LRU
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_items = max_items
        self.current_memory = 0

    def _estimate_size(self, value) -> int:
        """Estimate memory usage of cached object."""
        import sys

        if hasattr(value, "__sizeof__"):
            return value.__sizeof__()
        elif isinstance(value, (str, bytes)):
            return len(value) * (4 if isinstance(value, str) else 1)
        elif isinstance(value, dict):
            return sum(
                self._estimate_size(k) + self._estimate_size(v)
                for k, v in value.items()
            )
        elif isinstance(value, (list, tuple)):
            return sum(self._estimate_size(item) for item in value)
        else:
            return sys.getsizeof(value)

    def _evict_lru(self):
        """Evict least recently used items until under limits."""
        import time

        # Sort by access time (oldest first)
        if not self.access_order:
            return

        sorted_items = sorted(self.access_order.items(), key=lambda x: x[1])

        while (
            len(self.memory_cache) > self.max_items
            or self.current_memory > self.max_memory_bytes
        ) and sorted_items:
            key_to_remove = sorted_items.pop(0)[0]
            if key_to_remove in self.memory_cache:
                value = self.memory_cache[key_to_remove]
                self.current_memory -= self._estimate_size(value)
                del self.memory_cache[key_to_remove]
                del self.access_order[key_to_remove]

    def get(self, key: str) -> Any | None:
        """Get item from memory cache with LRU tracking."""
        import time

        if key in self.memory_cache:
            self.access_order[key] = time.time()
            return self.memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set item in memory cache with bounds checking."""
        import time

        value_size = self._estimate_size(value)

        # Don't cache items that are too large
        if value_size > self.max_memory_bytes * 0.5:
            logger.warning(f"Item too large to cache: {value_size} bytes")
            return

        # Update existing item
        if key in self.memory_cache:
            old_size = self._estimate_size(self.memory_cache[key])
            self.current_memory -= old_size

        self.memory_cache[key] = value
        self.current_memory += value_size
        self.access_order[key] = time.time()

        # Evict if necessary
        self._evict_lru()

    def clear(self) -> None:
        """Clear all cached items."""
        self.memory_cache.clear()
        self.access_order.clear()
        self.current_memory = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "items": len(self.memory_cache),
            "memory_mb": self.current_memory / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            "max_items": self.max_items,
        }

    def get_file_hash(self, file_path: Path) -> str:
        """Generate hash for file caching."""
        stat = file_path.stat()
        return hashlib.md5(
            f"{file_path}_{stat.st_mtime}_{stat.st_size}".encode()
        ).hexdigest()


class MatchEngineV2:
    """Enhanced matching engine with optimized performance and workflow."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()

        # Initialize ASR provider (singleton pattern for Parakeet optimization)
        logger.info(f"Initializing ASR provider: {config.asr_provider}")
        self.asr = get_asr_provider(config.asr_provider)
        # Pre-load the model to avoid repeated loading delays
        self.asr.load()
        logger.success("ASR provider loaded and ready")

        # Initialize cache manager for enhanced caching
        self.cache = CacheManager(config.cache_dir)

        # Initialize subtitle providers with fallback chain
        self._init_subtitle_providers()

        # Initialize matcher
        self.matcher = MultiSegmentMatcher(self.asr)

    def _init_subtitle_providers(self):
        """Initialize subtitle providers with fallback chain."""
        providers = []

        # Always include local provider first
        providers.append(LocalSubtitleProvider(self.config.cache_dir))

        # Add OpenSubtitles provider if enabled
        if self.config.sub_provider == "opensubtitles":
            providers.append(OpenSubtitlesProvider())
            logger.info("OpenSubtitles provider enabled")

        self.subtitle_provider = CompositeSubtitleProvider(providers)

    def scan_for_mkv(
        self, path: Path, recursive: bool = True
    ) -> Generator[Path, None, None]:
        """Scan for MKV files with optional recursive search."""
        if path.is_file() and path.suffix.lower() == ".mkv":
            yield path
        elif path.is_dir():
            if recursive:
                for p in path.rglob("*.mkv"):
                    yield p
            else:
                for p in path.glob("*.mkv"):
                    yield p

    def _detect_context(self, video_file: Path) -> tuple[str | None, int | None]:
        """Detect show name and season from file path using multiple heuristics."""
        show_name = None
        season = None

        # Heuristic 1: Standard folder structure (Show/Season X/file.mkv)
        try:
            parent_name = video_file.parent.name
            if "season" in parent_name.lower():
                # Extract season number
                s_match = re.search(r"(\d+)", parent_name)
                if s_match:
                    season = int(s_match.group(1))
                    show_name = video_file.parent.parent.name
        except Exception:
            pass

        # Heuristic 2: Season folder with S## pattern
        if not season:
            try:
                parent_name = video_file.parent.name
                s_match = re.search(r"[Ss](\d{1,2})", parent_name)
                if s_match:
                    season = int(s_match.group(1))
                    show_name = video_file.parent.parent.name
            except Exception:
                pass

        # Heuristic 3: Show directory structure (if config.show_dir is set)
        if not show_name and self.config.show_dir:
            try:
                if str(self.config.show_dir) in str(video_file):
                    rel = video_file.relative_to(self.config.show_dir)
                    if len(rel.parts) >= 2:  # show/season/file.mkv
                        show_name = rel.parts[0]
                        season_part = rel.parts[1]
                        if "season" in season_part.lower():
                            s_match = re.search(r"(\d+)", season_part)
                            if s_match:
                                season = int(s_match.group(1))
            except Exception:
                pass

        # Heuristic 4: Extract from filename itself
        if not season:
            filename = video_file.stem
            # Look for S##E## or ##x## patterns
            patterns = [
                r"[Ss](\d{1,2})[Ee]\d{1,2}",  # S01E01
                r"(\d{1,2})x\d{1,2}",  # 1x01
                r"Season[\s\.]*(\d{1,2})",  # Season 1
            ]
            for pattern in patterns:
                match = re.search(pattern, filename)
                if match:
                    season = int(match.group(1))
                    break

        # Clean show name
        if show_name:
            show_name = re.sub(r"[^\w\s-]", "", show_name).strip()

        return show_name, season

    def _is_already_processed(self, video_file: Path) -> bool:
        """Check if file is already processed (has SXXEXX format in filename)."""
        filename = video_file.stem
        # Check for S##E## pattern
        if re.search(r"[Ss]\d{1,2}[Ee]\d{1,2}", filename):
            return True
        # Check for ##x## pattern
        if re.search(r"\d{1,2}x\d{1,2}", filename):
            return True
        return False

    def _group_files_by_series(
        self, files: list[Path], season_override: int | None
    ) -> dict[tuple[str, int], list[Path]]:
        """Group files by series and season for batch processing."""
        groups = {}
        skipped = []

        for video_file in files:
            # Check if file is already processed
            if self._is_already_processed(video_file):
                logger.info(f"Skipping already processed file: {video_file.name}")
                skipped.append(video_file)
                continue

            show_name, season = self._detect_context(video_file)

            if season_override:
                season = season_override

            if not show_name or not season:
                logger.warning(f"Could not determine context for {video_file.name}")
                continue

            key = (show_name, season)
            if key not in groups:
                groups[key] = []
            groups[key].append(video_file)

        if skipped:
            logger.info(f"Skipped {len(skipped)} already processed files")

        return groups

    def _get_subtitles_with_fallback(
        self, show_name: str, season: int, video_files: list[Path] = None
    ):
        """Get subtitles with fallback chain (local -> subliminal)."""
        # Try to get from cache first
        cache_key = f"subtitles_{show_name}_{season}"
        cached_subs = self.cache.get(cache_key)
        if cached_subs:
            logger.debug(f"Using cached subtitles for {show_name} S{season:02d}")
            return cached_subs

        # Get subtitles from providers (pass video files for Subliminal)
        logger.info(f"Fetching subtitles for {show_name} S{season:02d}")
        subs = self.subtitle_provider.get_subtitles(show_name, season, video_files)

        # Cache results
        if subs:
            self.cache.set(cache_key, subs)
            logger.success(
                f"Found {len(subs)} subtitle files for {show_name} S{season:02d}"
            )
        else:
            logger.warning(f"No subtitles found for {show_name} S{season:02d}")

        return subs

    def _perform_rename(
        self, match: MatchResult, output_dir: Path | None = None
    ) -> Path | None:
        """Perform file rename with enhanced logic and output directory support."""
        original_path = match.matched_file

        # Generate new filename
        title_part = (
            f" - {match.episode_info.title}" if match.episode_info.title else ""
        )
        new_filename = f"{match.episode_info.series_name} - {match.episode_info.s_e_format}{title_part}{original_path.suffix}"

        # Clean filename
        new_filename = re.sub(r'[<>:"/\\\\|?*]', "", new_filename).strip()

        # Determine output path
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            new_path = output_dir / new_filename
        else:
            new_path = original_path.parent / new_filename

        if new_path == original_path:
            logger.debug("File already named correctly")
            return new_path

        try:
            if new_path.exists():
                logger.warning(f"Destination exists: {new_path}")
                return None

            if output_dir:
                # Copy to output directory
                import shutil

                shutil.copy2(original_path, new_path)
            else:
                # Rename in place
                original_path.rename(new_path)

            logger.success(
                f"{'Copied' if output_dir else 'Renamed'} to: {new_filename}"
            )
            match.matched_file = new_path
            return new_path

        except Exception as e:
            logger.error(
                f"Failed to {'copy' if output_dir else 'rename'} {original_path.name}: {e}"
            )
            return None

    def process_path(
        self,
        path: Path,
        season_override: int | None = None,
        recursive: bool = True,
        dry_run: bool = False,
        output_dir: Path | None = None,
        json_output: bool = False,
        confidence_threshold: float = None,
        progress_callback=None,
    ) -> tuple[list[MatchResult], list]:
        """
        Process path for MKV files with enhanced workflow and progress tracking.

        Args:
            path: Path to file or directory to process
            season_override: Force specific season number
            recursive: Whether to search recursively in directories
            dry_run: If True, don't actually rename files
            output_dir: Directory to copy renamed files to (instead of renaming in place)
            json_output: If True, suppress rich console output for JSON mode
            confidence_threshold: Minimum confidence score for matches

        Returns:
            Tuple of (successful matches, failed matches)
        """
        if confidence_threshold is None:
            confidence_threshold = self.config.min_confidence

        results = []
        failures = []
        files = list(self.scan_for_mkv(path, recursive))

        if not files:
            if not json_output:
                self.console.print(f"[yellow]No MKV files found in {path}[/yellow]")
            return []

        # Group files by series for batch processing
        file_groups = self._group_files_by_series(files, season_override)

        if not json_output:
            self.console.print(
                f"[blue]Found {len(files)} MKV files in {len(file_groups)} series/seasons[/blue]"
            )

        # Track total files for progress callback
        total_files = len(files)
        files_processed = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=self.console,
            disable=json_output,
        ) as progress:
            main_task = progress.add_task("Processing files...", total=total_files)

            for group_info, group_files in file_groups.items():
                show_name, season = group_info

                progress.update(
                    main_task, description=f"Processing {show_name} S{season:02d}"
                )

                # Get subtitles for this series/season (pass video files for Subliminal)
                subs = self._get_subtitles_with_fallback(show_name, season, group_files)

                if not subs:
                    if not json_output:
                        self.console.print(
                            f"[yellow]No subtitles found for {show_name} S{season:02d} - skipping {len(group_files)} files[/yellow]"
                        )
                    # Mark all files in group as failed
                    from mkv_episode_matcher.core.models import FailedMatch

                    for f in group_files:
                        failures.append(
                            FailedMatch(
                                original_file=f,
                                reason=f"No subtitles found for {show_name} S{season:02d}",
                                series_name=show_name,
                                season=season,
                            )
                        )
                        files_processed += 1
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(files_processed, total_files)
                    progress.advance(main_task, len(group_files))
                    continue

                # Process files in this group
                for video_file in group_files:
                    try:
                        match = self.matcher.match(video_file, subs)
                        if match and match.confidence >= confidence_threshold:
                            match.episode_info.series_name = show_name
                            results.append(match)

                            if not json_output:
                                self.console.print(
                                    f"[green]SUCCESS[/green] {video_file.name} -> "
                                    f"{match.episode_info.s_e_format} "
                                    f"(Confidence: {match.confidence:.2f})"
                                )

                            # Perform rename if not dry run
                            if not dry_run:
                                logger.debug(f"Attempting to rename {video_file.name}")
                                renamed_path = self._perform_rename(match, output_dir)
                                if renamed_path:
                                    match.matched_file = renamed_path
                                    logger.info(
                                        f"File successfully renamed: {video_file.name} -> {renamed_path.name}"
                                    )
                                else:
                                    logger.warning(
                                        f"Failed to rename {video_file.name}"
                                    )
                            else:
                                logger.debug(
                                    f"Dry run mode - skipping rename for {video_file.name}"
                                )

                        else:
                            if not json_output:
                                conf_str = (
                                    f" (conf: {match.confidence:.2f})" if match else ""
                                )
                                self.console.print(
                                    f"[red]FAILED[/red] {video_file.name} - No match{conf_str}"
                                )

                            from mkv_episode_matcher.core.models import FailedMatch

                            failures.append(
                                FailedMatch(
                                    original_file=video_file,
                                    reason=f"Low confidence match{f' ({match.confidence:.2f})' if match else ''} or no match found",
                                    confidence=match.confidence if match else 0.0,
                                    series_name=show_name,
                                    season=season,
                                )
                            )

                    except Exception as e:
                        logger.error(f"Error processing {video_file}: {e}")
                        if not json_output:
                            self.console.print(
                                f"[red]ERROR[/red] {video_file.name} - Error: {e}"
                            )

                    # Update progress after each file
                    files_processed += 1
                    if progress_callback:
                        # Only call progress callback every file to avoid overwhelming UI
                        progress_callback(files_processed, total_files)
                    progress.advance(main_task)

        return results, failures

    def export_results(self, results: list[MatchResult], format: str = "json") -> str:
        """Export results in various formats for automation."""
        if format == "json":
            export_data = []
            for result in results:
                export_data.append({
                    "original_file": str(result.matched_file),
                    "series_name": result.episode_info.series_name,
                    "season": result.episode_info.season,
                    "episode": result.episode_info.episode,
                    "episode_format": result.episode_info.s_e_format,
                    "title": result.episode_info.title,
                    "confidence": result.confidence,
                    "model_name": result.model_name,
                })
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def process_single_file(self, file_path: Path, **kwargs) -> MatchResult | None:
        """Process a single MKV file - convenience method."""
        matches, _ = self.process_path(file_path, **kwargs)
        return matches[0] if matches else None

    def process_library(self, library_path: Path, **kwargs) -> list[MatchResult]:
        """Process entire library - convenience method."""
        matches, _ = self.process_path(library_path, recursive=True, **kwargs)
        return matches


# Alias for backward compatibility
MatchEngine = MatchEngineV2
