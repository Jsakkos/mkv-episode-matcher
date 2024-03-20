# __main__.py
import argparse
import os
from .config import set_config, get_config

from loguru import logger
import sys

logger.remove()  # Remove the default stdout handler
logger.add("file_stdout_{time}.log", format="{time} {level} {message}", level="INFO", rotation="10 MB")  # Add a new handler for stdout logs
logger.add("file_stderr_{time}.log", format="{time} {level} {message}", level="ERROR", rotation="10 MB")  # Add a new handler for stderr logs

if not os.path.exists(os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher")):
    os.makedirs(os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher"))
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher","config.ini")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher","cache")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
def main():
    logger.info("Starting the application")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process shows with TMDb API")
    parser.add_argument("--api-key", help="TMDb API key")
    parser.add_argument("--show-dir", help="Main directory of the show")
    parser.add_argument("--season", type=int, default=None, nargs='?', help="Specify the season number to be processed (default: None)")
    parser.add_argument("--force", type=int, default=None, nargs='?', help="Force rename files (default: None)")
    parser.add_argument("--dry-run", type=int, default=None, nargs='?', help="Don't rename any files (default: None)")
    args = parser.parse_args()

    # Check if API key is provided via command-line argument
    api_key = args.api_key

    # If API key is not provided, try to get it from the cache
    if not api_key:
        cached_config = get_config(CONFIG_FILE)
        if cached_config:
            api_key = cached_config.get("api_key")

    # If API key is still not available, prompt the user to input it
    if not api_key:
        api_key = input("Enter your TMDb API key: ")
        # Cache the API key
    

    logger.debug(f"API Key: {api_key}")

    # If show directory is provided via command-line argument, use it
    show_dir = args.show_dir
    if not show_dir:
        show_dir = input("Enter the main directory of the show: ")
    logger.debug(f"Show Directory: {show_dir}")

    set_config(api_key, show_dir, CONFIG_FILE)
    logger.info("Configuration set")

    from .episode_matcher import process_show
    process_show(args.season,force=args.force,dry_run=args.dry_run)
    logger.info("Show processing completed")

if __name__ == "__main__":
    main()
