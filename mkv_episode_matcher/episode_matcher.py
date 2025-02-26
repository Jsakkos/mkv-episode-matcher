# mkv_episode_matcher/episode_matcher.py

from pathlib import Path
import shutil
import glob
import os
from loguru import logger
import re
from mkv_episode_matcher.__main__ import CONFIG_FILE, CACHE_DIR
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.tmdb_client import fetch_show_id
from mkv_episode_matcher.utils import (
    check_filename,
    clean_text,
    get_subtitles,
    get_valid_seasons,
    rename_episode_file,
    check_gpu_support
)
from mkv_episode_matcher.episode_identification import EpisodeMatcher

def process_show(season=None, dry_run=False, get_subs=False):
    """Process the show using streaming speech recognition."""
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = clean_text(os.path.basename(show_dir))
    matcher = EpisodeMatcher(CACHE_DIR, show_name)
    
    check_gpu_support()
    # Early check for reference files
    reference_dir = Path(CACHE_DIR) / "data" / show_name
    reference_files = list(reference_dir.glob("*.srt"))
    if (not get_subs) and (not reference_files):
        logger.error(f"No reference subtitle files found in {reference_dir}")
        logger.info("Please download reference subtitles first")
        return
        
    season_paths = get_valid_seasons(show_dir)
    if not season_paths:
        logger.warning(f"No seasons with .mkv files found")
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
        try:
            if get_subs:
                show_id = fetch_show_id(matcher.show_name)
                if show_id:
                    get_subtitles(show_id, seasons={season_num}, config=config)
            unmatched_files = []
            for mkv_file in mkv_files:
                logger.info(f"Attempting speech recognition match for {mkv_file}")
                match = matcher.identify_episode(mkv_file, season_num)
                
                if match:
                    new_name = f"{matcher.show_name} - S{match['season']:02d}E{match['episode']:02d}.mkv"
                    logger.info(f"Speech matched {os.path.basename(mkv_file)} to {new_name} "
                              f"(confidence: {match['confidence']:.2f})")
                    
                    if not dry_run:
                        logger.info(f"Renaming {mkv_file} to {new_name}")
                        rename_episode_file(mkv_file, new_name)
                else:
                    logger.warning(f"Speech recognition failed to match {mkv_file}")
                    unmatched_files.append(mkv_file)
                    
            # Notify about files that couldn't be matched
            if unmatched_files:
                logger.warning(f"Failed to match {len(unmatched_files)} files via speech recognition")
                for file in unmatched_files:
                    logger.info(f"  - {os.path.basename(file)}")
        except Exception as e:
            logger.error(f"Failed to process {season_path}: {e}")