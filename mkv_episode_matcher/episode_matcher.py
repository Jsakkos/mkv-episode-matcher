# mkv_episode_matcher/episode_matcher.py

import glob
import os
import re
import shutil
from pathlib import Path

from loguru import logger

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.episode_identification import EpisodeMatcher
from mkv_episode_matcher.tmdb_client import fetch_show_id
from mkv_episode_matcher.utils import (
    check_filename,
    clean_text,
    get_subtitles,
    get_valid_seasons,
    rename_episode_file,
)


def process_show(season=None, dry_run=False, get_subs=False):
    """Process the show using streaming speech recognition."""
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = clean_text(os.path.basename(show_dir))
    matcher = EpisodeMatcher(CACHE_DIR, show_name)

    # Early check for reference files
    reference_dir = Path(CACHE_DIR) / "data" / show_name
    reference_files = list(reference_dir.glob("*.srt"))
    if (not get_subs) and (not reference_files):
        logger.error(f"No reference subtitle files found in {reference_dir}")
        logger.info("Please download reference subtitles first")
        return

    season_paths = get_valid_seasons(show_dir)
    if not season_paths:
        logger.warning("No seasons with .mkv files found")
        return

    if season is not None:
        season_path = os.path.join(show_dir, f"Season {season}")
        if season_path not in season_paths:
            logger.warning(f"Season {season} has no .mkv files to process")
            return
        season_paths = [season_path]

    for season_path in season_paths:
        mkv_files = [f for f in glob.glob(os.path.join(season_path, "*.mkv"))
                    if not check_filename(f)]

        if not mkv_files:
            logger.info(f"No new files to process in {season_path}")
            continue

        season_num = int(re.search(r'Season (\d+)', season_path).group(1))
        temp_dir = Path(season_path) / "temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            if get_subs:
                show_id = fetch_show_id(matcher.show_name)
                if show_id:
                    get_subtitles(show_id, seasons={season_num}, config=config)

            for mkv_file in mkv_files:
                logger.info(f"Attempting speech recognition match for {mkv_file}")
                match = matcher.identify_episode(mkv_file, temp_dir, season_num)

                if match:
                    new_name = f"{matcher.show_name} - S{match['season']:02d}E{match['episode']:02d}.mkv"
                    logger.info(f"Speech matched {os.path.basename(mkv_file)} to {new_name} "
                              f"(confidence: {match['confidence']:.2f})")

                    if not dry_run:
                        logger.info(f"Renaming {mkv_file} to {new_name}")
                        rename_episode_file(mkv_file, new_name)
                else:
                    logger.info(f"Speech recognition match failed for {mkv_file}")
        finally:
            if not dry_run:
                shutil.rmtree(temp_dir)
