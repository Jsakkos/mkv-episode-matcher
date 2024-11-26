# mkv_episode_matcher/episode_matcher.py

from pathlib import Path
import shutil
import glob
import os
from loguru import logger

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
    compare_and_rename_files,get_valid_seasons
)
from mkv_episode_matcher.speech_to_text import process_speech_to_text
from mkv_episode_matcher.episode_identification import EpisodeMatcher

def process_show(season=None, dry_run=False, get_subs=False):
    """Process the show using both speech recognition and OCR fallback."""
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = clean_text(os.path.basename(show_dir))
    # Initialize episode matcher
    matcher = EpisodeMatcher(CACHE_DIR,show_name)
    
    # Get valid season directories
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

    # Process each season
    for season_path in season_paths:
        # Get MKV files that haven't been processed
        mkv_files = [f for f in glob.glob(os.path.join(season_path, "*.mkv"))
                    if not check_filename(f)]
        
        if not mkv_files:
            logger.info(f"No new files to process in {season_path}")
            continue

        # Create temp directories
        temp_dir = Path(season_path) / "temp"
        ocr_dir = Path(season_path) / "ocr"
        temp_dir.mkdir(exist_ok=True)
        ocr_dir.mkdir(exist_ok=True)

        try:
            # Download subtitles if requested
            if get_subs:
                show_id = fetch_show_id(matcher.series_name)
                if show_id:
                    seasons = {int(os.path.basename(p).split()[-1]) for p in season_paths}
                    get_subtitles(show_id, seasons=seasons)
            unmatched_files = []
            
            # First pass: Try speech recognition matching
            for mkv_file in mkv_files:
                logger.info(f"Attempting speech recognition match for {mkv_file}")
                
                # Extract audio and run speech recognition
                process_speech_to_text(mkv_file, str(temp_dir))
                match = matcher.identify_episode(mkv_file, temp_dir)
                
                if match and match['confidence'] >= matcher.min_confidence:
                    # Rename the file
                    new_name = f"{matcher.series_name} - S{match['season']:02d}E{match['episode']:02d}.mkv"
                    new_path = os.path.join(season_path, new_name)
                    
                    logger.info(f"Speech matched {os.path.basename(mkv_file)} to {new_name} "
                              f"(confidence: {match['confidence']:.2f})")
                    
                    if not dry_run:
                        os.rename(mkv_file, new_path)
                else:
                    logger.info(f"Speech recognition match failed for {mkv_file}, will try OCR")
                    unmatched_files.append(mkv_file)

            # Second pass: Try OCR for unmatched files
            if unmatched_files:
                logger.info(f"Attempting OCR matching for {len(unmatched_files)} unmatched files")
                
                # Convert files to SRT using OCR
                convert_mkv_to_srt(season_path, unmatched_files)
                
                # Process OCR results
                reference_text_dict = process_reference_srt_files(matcher.series_name)
                srt_text_dict = process_srt_files(str(ocr_dir))
                
                # Compare and rename
                compare_and_rename_files(
                    srt_text_dict, 
                    reference_text_dict, 
                    dry_run=dry_run,
                    min_confidence=0.1  # Lower threshold for OCR
                )
            


        finally:
            # Cleanup
            if not dry_run:
                shutil.rmtree(temp_dir)
                cleanup_ocr_files(show_dir)