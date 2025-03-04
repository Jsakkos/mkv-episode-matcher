# __main__.py
import argparse
import os

from loguru import logger

from mkv_episode_matcher import __version__
from mkv_episode_matcher.config import get_config, set_config

# Log the start of the application
logger.info("Starting the application")


# Check if the configuration directory exists, if not create it
if not os.path.exists(os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher")):
    os.makedirs(os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher"))

# Define the paths for the configuration file and cache directory
CONFIG_FILE = os.path.join(
    os.path.expanduser("~"), ".mkv-episode-matcher", "config.ini"
)
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher", "cache")

# Check if the cache directory exists, if not create it
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Check if logs directory exists, if not create it
log_dir = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher", "logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

# Add a new handler for stdout logs
logger.add(
    os.path.join(log_dir, "stdout.log"),
    format="{time} {level} {message}",
    level="INFO",
    rotation="10 MB",
)

# Add a new handler for error logs
logger.add(os.path.join(log_dir, "stderr.log"), level="ERROR", rotation="10 MB")


@logger.catch
def main():
    """
    Entry point of the application.

    This function is responsible for starting the application, parsing command-line arguments,
    setting the configuration, and processing the show.

    Command-line arguments:
    --tmdb-api-key: The API key for the TMDb API. If not provided, the function will try to get it from the cache or prompt the user to input it.
    --show-dir: The main directory of the show. If not provided, the function will prompt the user to input it.
    --season: The season number to be processed. If not provided, all seasons will be processed.
    --dry-run: A boolean flag indicating whether to perform a dry run (i.e., not rename any files). If not provided, the function will rename files.
    --get-subs: A boolean flag indicating whether to download subtitles for the show. If not provided, the function will not download subtitles.

    The function logs its progress to two separate log files: one for standard output and one for errors.
    """

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process shows with TMDb API")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version number and exit",
    )
    parser.add_argument("--tmdb-api-key", help="TMDb API key")
    parser.add_argument("--show-dir", help="Main directory of the show")
    parser.add_argument(
        "--season",
        type=int,
        default=None,
        nargs="?",
        help="Specify the season number to be processed (default: None)",
    )
    parser.add_argument(
        "--dry-run",
        type=bool,
        default=None,
        nargs="?",
        help="Don't rename any files (default: None)",
    )
    parser.add_argument(
        "--get-subs",
        type=bool,
        default=None,
        nargs="?",
        help="Download subtitles for the show (default: None)",
    )
    parser.add_argument(
        "--check-gpu",
        type=bool,
        default=False,
        nargs="?",
        help="Check if GPU is available (default: False)",
    )
    args = parser.parse_args()
    if args.check_gpu:
        from mkv_episode_matcher.utils import check_gpu_support

        check_gpu_support()
        return
    logger.debug(f"Command-line arguments: {args}")

    # Load configuration once
    config = get_config(CONFIG_FILE)

    # Get TMDb API key
    tmdb_api_key = args.tmdb_api_key or config.get("tmdb_api_key")

    logger.debug("Getting OpenSubtitles API key")
    open_subtitles_api_key = config.get("open_subtitles_api_key")
    open_subtitles_user_agent = config.get("open_subtitles_user_agent")
    open_subtitles_username = config.get("open_subtitles_username")
    open_subtitles_password = config.get("open_subtitles_password")

    if args.get_subs:
        if not tmdb_api_key:
            tmdb_api_key = input("Enter your TMDb API key: ")
        logger.debug(f"TMDb API Key: {tmdb_api_key}")
        if not open_subtitles_api_key:
            open_subtitles_api_key = input("Enter your OpenSubtitles API key: ")
        if not open_subtitles_user_agent:
            open_subtitles_user_agent = input("Enter your OpenSubtitles User Agent: ")
        if not open_subtitles_username:
            open_subtitles_username = input("Enter your OpenSubtitles Username: ")
        if not open_subtitles_password:
            open_subtitles_password = input("Enter your OpenSubtitles Password: ")

    # Use config for show directory
    show_dir = args.show_dir or config.get("show_dir")
    if not show_dir:
        show_dir = input("Enter the main directory of the show:")
    logger.info(f"Show Directory: {show_dir}")
    if not show_dir:
        show_dir = os.getcwd()

    logger.debug(f"Show Directory: {show_dir}")

    # Set the configuration
    set_config(
        tmdb_api_key,
        open_subtitles_api_key,
        open_subtitles_user_agent,
        open_subtitles_username,
        open_subtitles_password,
        show_dir,
        CONFIG_FILE,
    )
    logger.info("Configuration set")

    # Process the show
    from mkv_episode_matcher.episode_matcher import process_show

    process_show(args.season, dry_run=args.dry_run, get_subs=args.get_subs)
    logger.info("Show processing completed")


# Run the main function if the script is run directly
if __name__ == "__main__":
    main()
