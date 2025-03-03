# config.py
import configparser
import multiprocessing
import os

from loguru import logger

MAX_THREADS = 4


def get_total_threads():
    return multiprocessing.cpu_count()


total_threads = get_total_threads()

if total_threads < MAX_THREADS:
    MAX_THREADS = total_threads
logger.info(f"Total available threads: {total_threads} -> Setting max to {MAX_THREADS}")


def set_config(
    tmdb_api_key,
    open_subtitles_api_key,
    open_subtitles_user_agent,
    open_subtitles_username,
    open_subtitles_password,
    show_dir,
    file,
    tesseract_path=None,
):
    """
    Sets the configuration values and writes them to a file.

    Args:
        tmdb_api_key (str): The API key for TMDB (The Movie Database).
        open_subtitles_api_key (str): The API key for OpenSubtitles.
        open_subtitles_user_agent (str): The user agent for OpenSubtitles.
        open_subtitles_username (str): The username for OpenSubtitles.
        open_subtitles_password (str): The password for OpenSubtitles.
        show_dir (str): The directory where the TV show episodes are located.
        file (str): The path to the configuration file.
        tesseract_path (str, optional): The path to the Tesseract OCR executable.

    Returns:
        None
    """
    config = configparser.ConfigParser()
    config["Config"] = {
        "tmdb_api_key": str(tmdb_api_key),
        "show_dir": show_dir,
        "max_threads": int(MAX_THREADS),
        "open_subtitles_api_key": str(open_subtitles_api_key),
        "open_subtitles_user_agent": str(open_subtitles_user_agent),
        "open_subtitles_username": str(open_subtitles_username),
        "open_subtitles_password": str(open_subtitles_password),
        "tesseract_path": str(tesseract_path),
    }
    logger.info(
        f"Setting config with API:{tmdb_api_key}, show_dir: {show_dir}, and max_threads: {MAX_THREADS}"
    )
    with open(file, "w") as configfile:
        config.write(configfile)


def get_config(file):
    """
    Read and return the configuration from the specified file.

    Args:
        file (str): The path to the configuration file.

    Returns:
        dict: The configuration settings as a dictionary.

    """
    logger.info(f"Loading config from {file}")
    config = configparser.ConfigParser()
    if os.path.exists(file):
        config.read(file)
        return config["Config"] if "Config" in config else None
    return {}
