# __main__.py
import argparse
import os
from .config import set_config, get_config

from loguru import logger
import sys

# Remove the default stdout handler
logger.remove()  

# Check if logs directory exists, if not create it
if not os.path.exists('./logs'):
    os.mkdir('./logs')

# Add a new handler for stdout logs
logger.add("./logs/file_stdout.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB")  

# Add a new handler for error logs
logger.add("./logs/file_errors.log", level="ERROR", rotation="10 MB")  

# Check if the configuration directory exists, if not create it
if not os.path.exists(os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher")):
    os.makedirs(os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher"))

# Define the paths for the configuration file and cache directory
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher","config.ini")
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher","cache")

# Check if the cache directory exists, if not create it
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def main():
    """
    Entry point of the application.
    
    This function is responsible for starting the application, parsing command-line arguments,
    setting the configuration, and processing the show.

    Command-line arguments:
    --api-key: The API key for the TMDb API. If not provided, the function will try to get it from the cache or prompt the user to input it.
    --show-dir: The main directory of the show. If not provided, the function will prompt the user to input it.
    --season: The season number to be processed. If not provided, all seasons will be processed.
    --force: A boolean flag indicating whether to force rename files. If not provided, the function will not force rename files.
    --dry-run: A boolean flag indicating whether to perform a dry run (i.e., not rename any files). If not provided, the function will rename files.
    --threshold: The matching threshold for episode matching. If not provided, the function will use a default threshold.

    The function logs its progress to two separate log files: one for standard output and one for errors.
    """
    # Log the start of the application
    logger.info("Starting the application")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process shows with TMDb API")
    parser.add_argument("--api-key", help="TMDb API key")
    parser.add_argument("--show-dir", help="Main directory of the show")
    parser.add_argument("--season", type=int, default=None, nargs='?', help="Specify the season number to be processed (default: None)")
    parser.add_argument("--force", type=bool, default=None, nargs='?', help="Force rename files (default: None)")
    parser.add_argument("--dry-run", type=bool, default=None, nargs='?', help="Don't rename any files (default: None)")
    parser.add_argument("--threshold",type=int, default=None, nargs='?', help="Set matching threshold")
    parser.add_argument("--hash-type",type=str, default='average', nargs='?', help="Set hash type")
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

    # Set the configuration
    set_config(api_key, show_dir, CONFIG_FILE)
    logger.info("Configuration set")

    # Process the show
    from .episode_matcher import process_show
    process_show(args.season,force=args.force,dry_run=args.dry_run,threshold=args.threshold,hash_type=args.hash_type)
    logger.info("Show processing completed")

# Run the main function if the script is run directly
if __name__ == "__main__":
    main()