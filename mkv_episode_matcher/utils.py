# utils.py
import os
import re
import shutil
from pathlib import Path

import requests
import torch
from loguru import logger
from opensubtitlescom import OpenSubtitles
from opensubtitlescom.exceptions import OpenSubtitlesException
from rich.console import Console
from rich.panel import Panel

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.subtitle_utils import find_existing_subtitle, sanitize_filename
from mkv_episode_matcher.tmdb_client import fetch_season_details

console = Console()


def normalize_path(path_str):
    """
    Normalize a path string to handle cross-platform path issues.
    Properly handles trailing slashes and backslashes in both Windows and Unix paths.

    Args:
        path_str (str): The path string to normalize

    Returns:
        pathlib.Path: A normalized Path object
    """
    # Convert to string if it's a Path object
    if isinstance(path_str, Path):
        path_str = str(path_str)

    # Remove trailing slashes or backslashes
    path_str = path_str.rstrip("/").rstrip("\\")

    # Handle Windows paths on non-Windows platforms
    if os.name != "nt" and "\\" in path_str and ":" in path_str[:2]:
        # This looks like a Windows path on a non-Windows system
        # Extract the last component which should be the directory/file name
        components = path_str.split("\\")
        return Path(components[-1])

    return Path(path_str)


def get_valid_seasons(show_dir):
    """
    Get all season directories that contain MKV files.

    Args:
        show_dir (str): Base directory for the TV show

    Returns:
        list: List of paths to valid season directories
    """
    # Get all season directories
    show_path = normalize_path(show_dir)
    season_paths = [str(show_path / d.name) for d in show_path.iterdir() if d.is_dir()]

    # Filter seasons to only include those with .mkv files
    valid_season_paths = []
    for season_path in season_paths:
        season_path_obj = Path(season_path)
        mkv_files = [f for f in season_path_obj.iterdir() if f.name.endswith(".mkv")]
        if mkv_files:
            valid_season_paths.append(season_path)

    if not valid_season_paths:
        logger.warning(
            f"No seasons with .mkv files found in show '{normalize_path(show_dir).name}'"
        )
    else:
        logger.info(
            f"Found {len(valid_season_paths)} seasons with .mkv files in '{normalize_path(show_dir).name}'"
        )

    return valid_season_paths


def check_filename(filename):
    """
    Check if the filename is in the correct format (S01E02).

    Args:
        filename (str or Path): The filename to check.

    Returns:
        bool: True if the filename matches the expected pattern.
    """
    # Convert Path object to string if needed
    if isinstance(filename, Path):
        filename = str(filename)
    # Check if the filename matches the expected format
    match = re.search(r".*S\d+E\d+", filename)
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
    series_title = normalize_path(original_file_path).parent.parent.name
    original_file_name = Path(original_file_path).name
    extension = Path(original_file_path).suffix
    new_file_name = f"{series_title} - {file_number:03d}{extension}"
    new_file_path = Path(original_file_path).parent / new_file_name
    if not new_file_path.exists():
        logger.info(f"Renaming {original_file_name} -> {new_file_name}")
        Path(original_file_path).rename(new_file_path)


def rename_episode_file(original_file_path, new_filename):
    """
    Rename an episode file with a standardized naming convention.

    Args:
        original_file_path (str or Path): The original file path of the episode.
        new_filename (str or Path): The new filename including season/episode info.

    Returns:
        Path: Path to the renamed file, or None if rename failed.
    """
    original_dir = Path(original_file_path).parent
    new_file_path = original_dir / new_filename

    # Check if new filepath already exists
    if new_file_path.exists():
        logger.warning(f"File already exists: {new_filename}")

        # Add numeric suffix if file exists
        base, ext = Path(new_filename).stem, Path(new_filename).suffix
        suffix = 2
        while True:
            new_filename = f"{base}_{suffix}{ext}"
            new_file_path = original_dir / new_filename
            if not new_file_path.exists():
                break
            suffix += 1

    try:
        Path(original_file_path).rename(new_file_path)
        logger.info(f"Renamed {Path(original_file_path).name} -> {new_filename}")
        return new_file_path
    except OSError as e:
        logger.error(f"Failed to rename file: {e}")
        return None
    except FileExistsError as e:
        logger.error(f"Failed to rename file: {e}")
        return None


def get_subtitles(show_id, seasons: set[int], config=None, max_retries=3):
    """
    Retrieves and saves subtitles for a given TV show and seasons.

    Args:
        show_id (int): The ID of the TV show.
        seasons (Set[int]): A set of season numbers for which subtitles should be retrieved.
        config (Config object, optional): Preloaded configuration.
        max_retries (int, optional): Number of times to retry subtitle download on OpenSubtitlesException. Defaults to 3.
    """
    if config is None:
        config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    series_name = sanitize_filename(normalize_path(show_dir).name)
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

            series_cache_dir = Path(CACHE_DIR) / "data" / series_name
            os.makedirs(series_cache_dir, exist_ok=True)

            # Check for existing subtitle in any supported format
            existing_subtitle = find_existing_subtitle(
                series_cache_dir, series_name, season, episode
            )

            if existing_subtitle:
                logger.info(f"Subtitle already exists: {Path(existing_subtitle).name}")
                continue

            # Default to standard format for new downloads
            srt_filepath = str(
                series_cache_dir / f"{series_name} - S{season:02d}E{episode:02d}.srt"
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
                filename_clean = re.sub(
                    r"\\W+", " ", subtitle_dict["file_name"]
                ).upper()
                if f"E{episode:02d}" in filename_clean:
                    logger.info(f"Original filename: {subtitle_dict['file_name']}")
                    retry_count = 0
                    while retry_count < max_retries:
                        try:
                            srt_file = subtitles.download_and_save(subtitle)
                            shutil.move(srt_file, srt_filepath)
                            logger.info(f"Subtitle saved to {srt_filepath}")
                            break
                        except OpenSubtitlesException as e:
                            retry_count += 1
                            logger.error(
                                f"OpenSubtitlesException (attempt {retry_count}): {e}"
                            )
                            console.print(
                                f"[red]OpenSubtitlesException (attempt {retry_count}): {e}[/red]"
                            )
                            if retry_count >= max_retries:
                                user_input = input(
                                    "Would you like to continue matching? (y/n): "
                                )
                                if user_input.strip().lower() != "y":
                                    logger.info(
                                        "User chose to stop matching due to the error."
                                    )
                                    return
                                else:
                                    logger.info(
                                        "User chose to continue matching despite the error."
                                    )
                                    break
                        except Exception as e:
                            logger.error(f"Failed to download and save subtitle: {e}")
                            console.print(
                                f"[red]Failed to download and save subtitle: {e}[/red]"
                            )
                            user_input = input(
                                "Would you like to continue matching despite the error? (y/n): "
                            )
                            if user_input.strip().lower() != "y":
                                logger.info(
                                    "User chose to stop matching due to the error."
                                )
                                return
                            else:
                                logger.info(
                                    "User chose to continue matching despite the error."
                                )
                                break
                    else:
                        continue
                    break


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

    reference_files = {}
    reference_dir = Path(CACHE_DIR) / "data" / series_name

    for dirpath, _, filenames in os.walk(reference_dir):
        for filename in filenames:
            if filename.lower().endswith(".srt"):
                srt_file = Path(dirpath) / filename
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
    blocks = content.strip().split("\n\n")

    text_lines = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue

        # Skip index and timestamp, get all remaining lines as text
        text = " ".join(lines[2:])
        # Remove stage directions and tags
        text = re.sub(r"\[.*?\]|\<.*?\>", "", text)
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
        r"S(\d+)E(\d+)",  # S01E01
        r"(\d+)x(\d+)",  # 1x01 or 01x01
        r"Season\s*(\d+).*?(\d+)",  # Season 1 - 01
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
                srt_file = Path(dirpath) / filename
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
        parent_dir = Path(srt_text).parent.parent
        for reference in reference_files.keys():
            _season, _episode = extract_season_episode(reference)
            mkv_file = str(parent_dir / Path(srt_text).name.replace(".srt", ".mkv"))
            matching_lines = compare_text(
                reference_files[reference], srt_files[srt_text]
            )
            if matching_lines >= int(len(reference_files[reference]) * 0.1):
                logger.info(f"Matching lines: {matching_lines}")
                logger.info(f"Found matching file: {mkv_file} ->{reference}")
                new_filename = parent_dir / reference
                if not dry_run:
                    logger.info(f"Renaming {mkv_file} to {str(new_filename)}")
                    rename_episode_file(mkv_file, reference)


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


def check_gpu_support():
    logger.info("Checking GPU support...")
    console.print("[bold]Checking GPU support...[/bold]")
    if torch.cuda.is_available():
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
        console.print(
            Panel.fit(
                f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}",
                title="GPU Support",
                border_style="magenta",
            )
        )
    else:
        logger.warning(
            "CUDA not available. Using CPU. Refer to https://pytorch.org/get-started/locally/ for GPU support."
        )
        console.print(
            Panel.fit(
                "CUDA not available. Using CPU. Refer to https://pytorch.org/get-started/locally/ for GPU support.",
                title="GPU Support",
                border_style="red",
            )
        )
