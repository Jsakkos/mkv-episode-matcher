# __main__.py
import argparse
import os
from config import set_config, get_config
from loguru import logger

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".your_application_config.ini")

def main():
    logger.info("Starting the application")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process shows with TMDb API")
    parser.add_argument("--api-key", help="TMDb API key")
    parser.add_argument("--show-dir", help="Main directory of the show")
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
        set_config(api_key, args.show_dir, CONFIG_FILE)

    logger.debug(f"API Key: {api_key}")

    # If show directory is provided via command-line argument, use it
    show_dir = args.show_dir
    if not show_dir:
        show_dir = input("Enter the main directory of the show: ")
    logger.debug(f"Show Directory: {show_dir}")

    set_config(api_key, show_dir, CONFIG_FILE)
    logger.info("Configuration set")

    from episode_matcher import process_show
    process_show()
    logger.info("Show processing completed")

if __name__ == "__main__":
    main()
