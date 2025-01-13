# mkv_episode_matcher/episode_matcher.py

from pathlib import Path
import shutil
import glob
import os
from loguru import logger
import re
from mkv_episode_matcher.__main__ import CONFIG_FILE, CACHE_DIR
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.mkv_to_srt import convert_mkv_to_srt
from mkv_episode_matcher.tmdb_client import fetch_show_id
from mkv_episode_matcher.utils import (
    check_filename,
    clean_text,
    cleanup_ocr_files,
    get_subtitles,
    process_reference_srt_files,
    process_srt_files,
    compare_and_rename_files,get_valid_seasons,rename_episode_file
)
from mkv_episode_matcher.speech_to_text import process_speech_to_text
from mkv_episode_matcher.episode_identification import EpisodeMatcher

def process_show(season=None, dry_run=False, get_subs=False):
    """Process the show using streaming speech recognition with OCR fallback."""
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = clean_text(os.path.basename(show_dir))
    matcher = EpisodeMatcher(CACHE_DIR, show_name)
    
    # Early check for reference files
    reference_dir = Path(CACHE_DIR) / "data" / show_name
    reference_files = list(reference_dir.glob("*.srt"))
    if not reference_files:
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
        temp_dir = Path(season_path) / "temp"
        ocr_dir = Path(season_path) / "ocr"
        temp_dir.mkdir(exist_ok=True)
        ocr_dir.mkdir(exist_ok=True)

        try:
            if get_subs:
                show_id = fetch_show_id(matcher.show_name)
                if show_id:
                    get_subtitles(show_id, seasons={season_num})
                    
            unmatched_files = []
            for mkv_file in mkv_files:
                logger.info(f"Attempting speech recognition match for {mkv_file}")
                match = matcher.identify_episode(mkv_file, temp_dir, season_num)
                
                if match:
                    new_name = f"{matcher.show_name} - S{match['season']:02d}E{match['episode']:02d}.mkv"
                    new_path = os.path.join(season_path, new_name)
                    
                    logger.info(f"Speech matched {os.path.basename(mkv_file)} to {new_name} "
                              f"(confidence: {match['confidence']:.2f})")
                    
                    if not dry_run:
                        logger.info(f"Renaming {mkv_file} to {new_name}")
                        rename_episode_file(mkv_file, new_name)
                else:
                    logger.info(f"Speech recognition match failed for {mkv_file}, trying OCR")
                    unmatched_files.append(mkv_file)

            # OCR fallback for unmatched files
            if unmatched_files:
                logger.info(f"Attempting OCR matching for {len(unmatched_files)} unmatched files")
                convert_mkv_to_srt(season_path, unmatched_files)
                
                reference_text_dict = process_reference_srt_files(matcher.show_name)
                srt_text_dict = process_srt_files(str(ocr_dir))
                
                compare_and_rename_files(
                    srt_text_dict, 
                    reference_text_dict, 
                    dry_run=dry_run,
                )

        finally:
            if not dry_run:
                shutil.rmtree(temp_dir)
                cleanup_ocr_files(show_dir)