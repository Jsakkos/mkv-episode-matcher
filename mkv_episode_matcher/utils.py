# utils.py
import os
import re
import shutil

import requests
from loguru import logger
from opensubtitlescom import OpenSubtitles

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.tmdb_client import fetch_season_details
from mkv_episode_matcher.subtitle_utils import find_existing_subtitle,sanitize_filename
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


def scramble_filename(original_file_path, file_number):
    """
    Scrambles the filename of the given file path by adding the series title and file number.

    Args:
        original_file_path (str): The original file path.
        file_number (int): The file number to be added to the filename.

    Returns:
        None
    """
    logger.info(f"Scrambling {original_file_path}")
    series_title = os.path.basename(
        os.path.dirname(os.path.dirname(original_file_path))
    )
    original_file_name = os.path.basename(original_file_path)
    extension = os.path.splitext(original_file_path)[-1]
    new_file_name = f"{series_title} - {file_number:03d}{extension}"
    new_file_path = os.path.join(os.path.dirname(original_file_path), new_file_name)
    if not os.path.exists(new_file_path):
        logger.info(f"Renaming {original_file_name} -> {new_file_name}")
        os.rename(original_file_path, new_file_path)


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
        
def get_subtitles(show_id, seasons: set[int]):
    """
    Retrieves and saves subtitles for a given TV show and seasons.

    Args:
        show_id (int): The ID of the TV show.
        seasons (Set[int]): A set of season numbers for which subtitles should be retrieved.
    """
    logger.info(f"Getting subtitles for show ID {show_id}")
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
                    shutil.move(srt_file, srt_filepath)
                    logger.info(f"Subtitle saved to {srt_filepath}")
                    break


def cleanup_ocr_files(show_dir):
    """
    Clean up OCR files generated during the episode matching process.

    Args:
        show_dir (str): The directory containing the show files.

    Returns:
        None

    This function cleans up the OCR files generated during the episode matching process.
    It deletes the 'ocr' directory and all its contents in each season directory of the show.
    """
    for season_dir in os.listdir(show_dir):
        season_dir_path = os.path.join(show_dir, season_dir)
        ocr_dir_path = os.path.join(season_dir_path, "ocr")
        if os.path.exists(ocr_dir_path):
            logger.info(f"Cleaning up OCR files in {ocr_dir_path}")
            shutil.rmtree(ocr_dir_path)


def clean_text(text):
    # Remove brackets, parentheses, and their content
    cleaned_text = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", text)
    # Strip leading/trailing whitespace
    return cleaned_text.strip()

@logger.catch
def process_reference_srt_files(series_name):
    """
    Process reference SRT files for a given series.

    Args:
        series_name (str): The name of the series.

    Returns:
        dict: A dictionary containing the reference files where the keys are the MKV filenames
              and the values are the corresponding SRT texts.
    """
    from mkv_episode_matcher.__main__ import CACHE_DIR
    import os
    
    reference_files = {}
    reference_dir = os.path.join(CACHE_DIR, "data", series_name)
    
    for dirpath, _, filenames in os.walk(reference_dir):
        for filename in filenames:
            if filename.lower().endswith(".srt"):
                srt_file = os.path.join(dirpath, filename)
                logger.info(f"Processing {srt_file}")
                srt_text = extract_srt_text(srt_file)
                season, episode = extract_season_episode(filename)
                mkv_filename = f"{series_name} - S{season:02}E{episode:02}.mkv"
                reference_files[mkv_filename] = srt_text
                
    return reference_files

def extract_srt_text(filepath):
    """
    Extracts text content from an SRT file.

    Args:
        filepath (str): Path to the SRT file.

    Returns:
        list: List of text lines from the SRT file.
    """
    # Read the file content
    with open(filepath) as f:
        content = f.read()
        
    # Split into subtitle blocks
    blocks = content.strip().split('\n\n')
    
    text_lines = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) < 3:
            continue
            
        # Skip index and timestamp, get all remaining lines as text
        text = ' '.join(lines[2:])
        # Remove stage directions and tags
        text = re.sub(r'\[.*?\]|\<.*?\>', '', text)
        if text:
            text_lines.append(text)
            
    return text_lines

def extract_season_episode(filename):
    """
    Extract season and episode numbers from filename with support for multiple formats.
    
    Args:
        filename (str): Filename to parse
        
    Returns:
        tuple: (season_number, episode_number)
    """
    # List of patterns to try
    patterns = [
        r'S(\d+)E(\d+)',          # S01E01
        r'(\d+)x(\d+)',           # 1x01 or 01x01
        r'Season\s*(\d+).*?(\d+)' # Season 1 - 01
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))
            
    return None, None

def process_srt_files(show_dir):
    """
    Process all SRT files in the given directory and its subdirectories.

    Args:
        show_dir (str): The directory path where the SRT files are located.

    Returns:
        dict: A dictionary containing the SRT file paths as keys and their corresponding text content as values.
    """
    srt_files = {}
    for dirpath, _, filenames in os.walk(show_dir):
        for filename in filenames:
            if filename.lower().endswith(".srt"):
                srt_file = os.path.join(dirpath, filename)
                logger.info(f"Processing {srt_file}")
                srt_text = extract_srt_text(srt_file)
                srt_files[srt_file] = srt_text
    return srt_files
def compare_and_rename_files(srt_files, reference_files, dry_run=False):
    """
    Compare the srt files with the reference files and rename the matching mkv files.

    Args:
        srt_files (dict): A dictionary containing the srt files as keys and their contents as values.
        reference_files (dict): A dictionary containing the reference files as keys and their contents as values.
        dry_run (bool, optional): If True, the function will only log the renaming actions without actually renaming the files. Defaults to False.
    """
    logger.info(
        f"Comparing {len(srt_files)} srt files with {len(reference_files)} reference files"
    )
    for srt_text in srt_files.keys():
        parent_dir = os.path.dirname(os.path.dirname(srt_text))
        for reference in reference_files.keys():
            _season, _episode = extract_season_episode(reference)
            mkv_file = os.path.join(
                parent_dir, os.path.basename(srt_text).replace(".srt", ".mkv")
            )
            matching_lines = compare_text(
                reference_files[reference], srt_files[srt_text]
            )
            if matching_lines >= int(len(reference_files[reference]) * 0.1):
                logger.info(f"Matching lines: {matching_lines}")
                logger.info(f"Found matching file: {mkv_file} ->{reference}")
                new_filename = os.path.join(parent_dir, reference)
                if not dry_run:
                    logger.info(f"Renaming {mkv_file} to {new_filename}")
                    rename_episode_file(mkv_file, new_filename)

def compare_text(text1, text2):
    """
    Compare two lists of text lines and return the number of matching lines.

    Args:
        text1 (list): List of text lines from the first source.
        text2 (list): List of text lines from the second source.

    Returns:
        int: Number of matching lines between the two sources.
    """
    # Flatten the list of text lines
    flat_text1 = [line for lines in text1 for line in lines]
    flat_text2 = [line for lines in text2 for line in lines]

    # Compare the two lists of text lines
    matching_lines = set(flat_text1).intersection(flat_text2)
    return len(matching_lines)