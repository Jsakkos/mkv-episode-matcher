# utils.py
import os
import re
import torch
import requests
from loguru import logger
from opensubtitlescom import OpenSubtitles

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.tmdb_client import fetch_season_details
from mkv_episode_matcher.subtitle_utils import find_existing_subtitle, sanitize_filename

def get_valid_seasons(show_dir):
    """
    Get all season directories that contain MKV files.

    Args:
        show_dir (str): Base directory for the TV show

    Returns:
        list: List of paths to valid season directories
    """
    # Get all season directories
    season_paths = [
        os.path.join(show_dir, d)
        for d in os.listdir(show_dir)
        if os.path.isdir(os.path.join(show_dir, d))
    ]

    # Filter seasons to only include those with .mkv files
    valid_season_paths = []
    for season_path in season_paths:
        mkv_files = [f for f in os.listdir(season_path) if f.endswith(".mkv")]
        if mkv_files:
            valid_season_paths.append(season_path)

    if not valid_season_paths:
        logger.warning(f"No seasons with .mkv files found in show '{os.path.basename(show_dir)}'")
    else:
        logger.info(
            f"Found {len(valid_season_paths)} seasons with .mkv files in '{os.path.basename(show_dir)}'"
        )

    return valid_season_paths

def check_filename(filename):
    """
    Check if the filename is in the correct format (S01E02).

    Args:
        filename (str): The filename to check.

    Returns:
        bool: True if the filename matches the expected pattern.
    """
    # Check if the filename matches the expected format
    match = re.search(r'.*S\d+E\d+', filename)
    return bool(match)

def rename_episode_file(original_file_path, new_filename):
    """
    Rename an episode file with a standardized naming convention.

    Args:
        original_file_path (str): The original file path of the episode.
        new_filename (str): The new filename including season/episode info.

    Returns:
        str: Path to the renamed file, or None if rename failed.
    """
    original_dir = os.path.dirname(original_file_path)
    new_file_path = os.path.join(original_dir, new_filename)
    
    # Check if new filepath already exists
    if os.path.exists(new_file_path):
        logger.warning(f"File already exists: {new_filename}")
        
        # Add numeric suffix if file exists
        base, ext = os.path.splitext(new_filename)
        suffix = 2
        while True:
            new_filename = f"{base}_{suffix}{ext}"
            new_file_path = os.path.join(original_dir, new_filename)
            if not os.path.exists(new_file_path):
                break
            suffix += 1
    
    try:
        os.rename(original_file_path, new_file_path)
        logger.info(f"Renamed {os.path.basename(original_file_path)} -> {new_filename}")
        return new_file_path
    except OSError as e:
        logger.error(f"Failed to rename file: {e}")
        return None
    except FileExistsError as e:
        logger.error(f"Failed to rename file: {e}")
        return None
        
def get_subtitles(show_id, seasons: set[int], config=None):
    """
    Retrieves and saves subtitles for a given TV show and seasons.

    Args:
        show_id (int): The ID of the TV show.
        seasons (Set[int]): A set of season numbers for which subtitles should be retrieved.
        config (Config object, optional): Preloaded configuration.
    """
    if config is None:
        config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    series_name = sanitize_filename(os.path.basename(show_dir))
    tmdb_api_key = config.get("tmdb_api_key")
    open_subtitles_api_key = config.get("open_subtitles_api_key")
    open_subtitles_user_agent = config.get("open_subtitles_user_agent")
    open_subtitles_username = config.get("open_subtitles_username")
    open_subtitles_password = config.get("open_subtitles_password")

    if not all([
        show_dir,
        tmdb_api_key,
        open_subtitles_api_key,
        open_subtitles_user_agent,
        open_subtitles_username,
        open_subtitles_password,
    ]):
        logger.error("Missing configuration settings. Please run the setup script.")
        return

    try:
        subtitles = OpenSubtitles(open_subtitles_user_agent, open_subtitles_api_key)
        subtitles.login(open_subtitles_username, open_subtitles_password)
    except Exception as e:
        logger.error(f"Failed to log in to OpenSubtitles: {e}")
        return

    for season in seasons:
        episodes = fetch_season_details(show_id, season)
        logger.info(f"Found {episodes} episodes in Season {season}")

        for episode in range(1, episodes + 1):
            logger.info(f"Processing Season {season}, Episode {episode}...")
            
            series_cache_dir = os.path.join(CACHE_DIR, "data", series_name)
            os.makedirs(series_cache_dir, exist_ok=True)
            
            # Check for existing subtitle in any supported format
            existing_subtitle = find_existing_subtitle(
                series_cache_dir, series_name, season, episode
            )
            
            if existing_subtitle:
                logger.info(f"Subtitle already exists: {os.path.basename(existing_subtitle)}")
                continue
                
            # Default to standard format for new downloads
            srt_filepath = os.path.join(
                series_cache_dir,
                f"{series_name} - S{season:02d}E{episode:02d}.srt",
            )

            # get the episode info from TMDB
            url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season}/episode/{episode}?api_key={tmdb_api_key}"
            response = requests.get(url)
            response.raise_for_status()
            episode_data = response.json()
            episode_id = episode_data["id"]
            
            # search for the subtitle
            response = subtitles.search(tmdb_id=episode_id, languages="en")
            if len(response.data) == 0:
                logger.warning(
                    f"No subtitles found for {series_name} - S{season:02d}E{episode:02d}"
                )
                continue

            for subtitle in response.data:
                subtitle_dict = subtitle.to_dict()
                # Remove special characters and convert to uppercase
                filename_clean = re.sub(r"\W+", " ", subtitle_dict["file_name"]).upper()
                if f"E{episode:02d}" in filename_clean:
                    logger.info(f"Original filename: {subtitle_dict['file_name']}")
                    srt_file = subtitles.download_and_save(subtitle)
                    os.rename(srt_file, srt_filepath)
                    logger.info(f"Subtitle saved to {srt_filepath}")
                    break

def clean_text(text):
    # Remove brackets, parentheses, and their content
    cleaned_text = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", text)
    # Strip leading/trailing whitespace
    return cleaned_text.strip()

def check_gpu_support():
    logger.info('Checking GPU support...')
    if torch.cuda.is_available():
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        logger.warning("CUDA not available. Using CPU. Refer to https://pytorch.org/get-started/locally/ for GPU support.")