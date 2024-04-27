# utils.py
import os
import re
import shutil
from typing import Set

import requests
from loguru import logger
from opensubtitlescom import OpenSubtitles

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.tmdb_client import fetch_season_details


def check_filename(filename, series_title, season_number, episode_number):
    """
    Check if a filename matches the expected naming convention for a series episode.

    Args:
        filename (str): The filename to be checked.
        series_title (str): The title of the series.
        season_number (int): The season number of the episode.
        episode_number (int): The episode number of the episode.

    Returns:
        bool: True if the filename matches the expected naming convention, False otherwise.

    This function checks if the given filename matches the expected naming convention for a series episode.
    The expected naming convention is '{series_title} - S{season_number:02d}E{episode_number:02d}.mkv'.
    If the filename matches the expected pattern, it returns True; otherwise, it returns False.

    Example:
        If filename = 'Example - S01E03.mkv', series_title = 'Example', season_number = 1, and episode_number = 3,
        the function will return True because the filename matches the expected pattern.
    """
    pattern = re.compile(
        f"{re.escape(series_title)} - S{season_number:02d}E{episode_number:02d}.mkv"
    )
    return bool(pattern.match(filename))


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


def rename_episode_file(original_file_path, season_number, episode_number):
    """
    Rename an episode file with a standardized naming convention.

    Args:
        original_file_path (str): The original file path of the episode.
        season_number (int): The season number of the episode.
        episode_number (int): The episode number of the episode.

    Returns:
        None

    This function renames an episode file with a standardized naming convention based on the series title, season number,
    and episode number. If a file with the intended new name already exists, it appends a numerical suffix to the filename
    until it finds a unique name.

    Example:
        If original_file_path = '/path/to/episode.mkv', season_number = 1, and episode_number = 3, and the series title is 'Example',
        the function will rename the file to 'Example - S01E03.mkv' if no file with that name already exists. If a file with that
        name already exists, it will be renamed to 'Example - S01E03_2.mkv', and so on.
    """
    series_title = os.path.basename(
        os.path.dirname(os.path.dirname(original_file_path))
    )
    original_file_name = os.path.basename(original_file_path)
    extension = os.path.splitext(original_file_path)[-1]
    new_file_name = (
        f"{series_title} - S{season_number:02d}E{episode_number:02d}{extension}"
    )
    new_file_path = os.path.join(os.path.dirname(original_file_path), new_file_name)

    # Check if the new file path already exists
    if os.path.exists(new_file_path):
        logger.warning(f"Filename already exists: {new_file_name}.")

        # If the file already exists, find a unique name by appending a numerical suffix
        suffix = 2
        while True:
            new_file_name = f"{series_title} - S{season_number:02d}E{episode_number:02d}_{suffix}{extension}"
            new_file_path = os.path.join(
                os.path.dirname(original_file_path), new_file_name
            )
            if not os.path.exists(new_file_path):
                break
            suffix += 1

        logger.info(f"Renaming {original_file_name} -> {new_file_name}")
        os.rename(original_file_path, new_file_path)
    else:
        logger.info(f"Renaming {original_file_name} -> {new_file_name}")
        os.rename(original_file_path, new_file_path)


def get_subtitles(show_id, seasons: Set[int]):
    """
    Retrieves and saves subtitles for a given TV show and seasons.

    Args:
        show_id (int): The ID of the TV show.
        seasons (Set[int]): A set of season numbers for which subtitles should be retrieved.

    Returns:
        None
    """

    logger.info(f"Getting subtitles for show ID {show_id}")
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    series_name = os.path.basename(show_dir)
    tmdb_api_key = config.get("tmdb_api_key")
    open_subtitles_api_key = config.get("open_subtitles_api_key")
    open_subtitles_user_agent = config.get("open_subtitles_user_agent")
    open_subtitles_username = config.get("open_subtitles_username")
    open_subtitles_password = config.get("open_subtitles_password")
    if not all(
        [
            show_dir,
            tmdb_api_key,
            open_subtitles_api_key,
            open_subtitles_user_agent,
            open_subtitles_username,
            open_subtitles_password,
        ]
    ):
        logger.error("Missing configuration settings. Please run the setup script.")
    try:
        # Initialize the OpenSubtitles client
        subtitles = OpenSubtitles(open_subtitles_user_agent, open_subtitles_api_key)

        # Log in (retrieve auth token)
        subtitles.login(open_subtitles_username, open_subtitles_password)
    except Exception as e:
        logger.error(f"Failed to log in to OpenSubtitles: {e}")
        return
    for season in seasons:
        episodes = fetch_season_details(show_id, season)
        logger.info(f"Found {episodes} episodes in Season {season}")

        for episode in range(1, episodes + 1):
            logger.info(f"Processing Season {season}, Episode {episode}...")
            srt_filepath = os.path.join(
                CACHE_DIR,
                "data",
                series_name,
                f"{series_name} - S{season:02d}E{episode:02d}.srt",
            )
            if not os.path.exists(srt_filepath):
                # get the episode info from TMDB
                url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season}/episode/{episode}?api_key={tmdb_api_key}"
                response = requests.get(url)
                response.raise_for_status()
                episode_data = response.json()
                episode_name = episode_data["name"]
                episode_id = episode_data["id"]
                # search for the subtitle
                response = subtitles.search(tmdb_id=episode_id, languages="en")
                if len(response.data) == 0:
                    logger.warning(
                        f"No subtitles found for {series_name} - S{season:02d}E{episode:02d}"
                    )

                for subtitle in response.data:
                    subtitle_dict = subtitle.to_dict()
                    # Remove special characters and convert to uppercase
                    filename_clean = re.sub(
                        r"\W+", " ", subtitle_dict["file_name"]
                    ).upper()
                    if f"E{episode:02d}" in filename_clean:
                        logger.info(f"Original filename: {subtitle_dict['file_name']}")
                        srt_file = subtitles.download_and_save(subtitle)
                        series_name = series_name.replace(":", " -")
                        shutil.move(srt_file, srt_filepath)
                        logger.info(f"Subtitle saved to {srt_filepath}")
                        break
                    else:
                        continue
            else:
                logger.info(
                    f"Subtitle already exists for {series_name} - S{season:02d}E{episode:02d}"
                )
                continue


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
