# episode_matcher.py
import os
import re

from loguru import logger

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.mkv_to_srt import convert_mkv_to_srt
from mkv_episode_matcher.tmdb_client import fetch_show_id
from mkv_episode_matcher.utils import (
    check_filename,
    clean_text,
    cleanup_ocr_files,
    get_subtitles,
)


# hash_data = {}
@logger.catch
def process_show(season=None, dry_run=False, get_subs=False):
    """
    Process the show by downloading episode images and finding matching episodes.
    Args:
        season (int, optional): The season number to process. If provided, only that season will be processed. Defaults to None.
        dry_run (bool, optional): Whether to perform a dry run without actually processing the episodes. Defaults to False.
        get_subs (bool, optional): Whether to download subtitles for the episodes. Defaults to False.
    """
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = clean_text(os.path.basename(show_dir))
    logger.info(f"Processing show '{show_name}'...")

    show_id = fetch_show_id(show_name)
    if show_id is None:
        logger.error(f"Could not find show '{os.path.basename(show_dir)}' on TMDb.")
        return

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
        logger.warning(f"No seasons with .mkv files found in show '{show_name}'")
        return

    logger.info(
        f"Found {len(valid_season_paths)} seasons with .mkv files for show '{show_name}'"
    )

    # Extract season numbers from valid paths
    seasons_to_process = [
        int(os.path.basename(season_path).split()[-1])
        for season_path in valid_season_paths
    ]

    if get_subs:
        get_subtitles(show_id, seasons=set(seasons_to_process))

    if season is not None:
        # If specific season requested, check if it has .mkv files
        season_path = os.path.join(show_dir, f"Season {season}")
        if season_path not in valid_season_paths:
            logger.warning(f"Season {season} has no .mkv files to process")
            return

        season_paths_to_process = [season_path]
    else:
        # Process all valid seasons
        season_paths_to_process = valid_season_paths

    # Process each season
    for season_path in season_paths_to_process:
        logger.info(f"Processing season path: {season_path}")
        mkv_files = [
            os.path.join(season_path, f)
            for f in os.listdir(season_path)
            if f.endswith(".mkv")
        ]
        
        # Filter out files that have already been processed
        unprocessed_files = []
        for f in mkv_files:
            if check_filename(f):
                logger.info(f"Skipping {f}, already processed")
            else:
                unprocessed_files.append(f)

        if not unprocessed_files:
            logger.info(f"No new files to process in {season_path}")
            continue

        logger.info(f"Processing {len(unprocessed_files)} files in {season_path}")
        convert_mkv_to_srt(season_path, unprocessed_files)
        
    # Process reference and SRT files after all seasons are converted
    reference_text_dict = process_reference_srt_files(show_name)
    srt_text_dict = process_srt_files(show_dir)
    compare_and_rename_files(srt_text_dict, reference_text_dict, dry_run=dry_run)
    cleanup_ocr_files(show_dir)


def check_filename(filename):
    """
    Check if the filename is in the correct format.

    Args:
        filename (str): The filename to check.

    Returns:
        bool: True if the filename is in the correct format, False otherwise.
    """
    # Check if the filename matches the expected format
    match = re.match(r".*S\d+E\d+", filename)
    return bool(match)


def extract_srt_text(filepath):
    """
    Extracts the text from an SRT file.

    Args:
        filepath (str): The path to the SRT file.

    Returns:
        list: A list of lists, where each inner list represents a block of text from the SRT file.
              Each inner list contains the lines of text for that block.
    """
    # extract the text from the file
    with open(filepath) as f:
        filepath = f.read()
    text_lines = [
        filepath.split("\n\n")[i].split("\n")[2:]
        for i in range(len(filepath.split("\n\n")))
    ]
    # remove empty lines
    text_lines = [[line for line in lines if line] for lines in text_lines]
    # remove <i> or </i> tags
    text_lines = [
        [re.sub(r"<i>|</i>|", "", line) for line in lines] for lines in text_lines
    ]
    # remove empty lists
    text_lines = [lines for lines in text_lines if lines]
    return text_lines


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


def extract_season_episode(filename):
    """
    Extract the season and episode number from the filename.

    Args:
        filename (str): The filename to extract the season and episode from.

    Returns:
        tuple: A tuple containing the season and episode number.
    """
    # Extract the season and episode number from the filename
    match = re.search(r"S(\d+)E(\d+)", filename)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return season, episode
    else:
        return None, None


def process_reference_srt_files(series_name):
    """
    Process reference SRT files for a given series.

    Args:
        series_name (str): The name of the series.

    Returns:
        dict: A dictionary containing the reference files where the keys are the MKV filenames
              and the values are the corresponding SRT texts.
    """
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
                if not os.path.exists(new_filename):
                    if os.path.exists(mkv_file) and not dry_run:
                        logger.info(f"Renaming {mkv_file} to {new_filename}")
                        os.rename(mkv_file, new_filename)
                else:
                    logger.info(f"File {new_filename} already exists, skipping")
