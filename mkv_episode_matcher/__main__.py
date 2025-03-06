# __main__.py (enhanced version)
import argparse
import os
import sys
from typing import Optional

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from mkv_episode_matcher import __version__
from mkv_episode_matcher.config import get_config, set_config

# Initialize rich console for better output
console = Console()

# Log the start of the application
logger.info("Starting the application")

# Check if the configuration directory exists, if not create it
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".mkv-episode-matcher")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Define the paths for the configuration file and cache directory
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
CACHE_DIR = os.path.join(CONFIG_DIR, "cache")

# Check if the cache directory exists, if not create it
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Check if logs directory exists, if not create it
log_dir = os.path.join(CONFIG_DIR, "logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
logger.remove()
# Add a new handler for stdout logs
logger.add(
    os.path.join(log_dir, "stdout.log"),
    format="{time} {level} {message}",
    level="INFO",
    rotation="10 MB",
)

# Add a new handler for error logs
logger.add(os.path.join(log_dir, "stderr.log"), level="ERROR", rotation="10 MB")


def print_welcome_message():
    """Print a stylized welcome message."""
    console.print(
        Panel.fit(
            f"[bold blue]MKV Episode Matcher v{__version__}[/bold blue]\n"
            "[cyan]Automatically match and rename your MKV TV episodes[/cyan]",
            border_style="blue",
            padding=(1, 4),
        )
    )
    console.print()


def confirm_api_key(config_value: Optional[str], key_name: str, description: str) -> str:
    """
    Confirm if the user wants to use an existing API key or enter a new one.
    
    Args:
        config_value: The current value from the config
        key_name: The name of the key
        description: Description of the key for user information
        
    Returns:
        The API key to use
    """
    if config_value:
        console.print(f"[cyan]{key_name}:[/cyan] {description}")
        console.print(f"Current value: [green]{mask_api_key(config_value)}[/green]")
        if Confirm.ask("Use existing key?", default=True):
            return config_value
    
    return Prompt.ask(f"Enter your {key_name}")


def mask_api_key(key: str) -> str:
    """Mask the API key for display purposes."""
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def select_season(seasons):
    """
    Allow user to select a season from a list.
    
    Args:
        seasons: List of available seasons
        
    Returns:
        Selected season number or None for all seasons
    """
    console.print("[bold cyan]Available Seasons:[/bold cyan]")
    for i, season in enumerate(seasons, 1):
        season_num = os.path.basename(season).replace("Season ", "")
        console.print(f"  {i}. Season {season_num}")
    
    console.print(f"  0. All Seasons")
    
    choice = Prompt.ask(
        "Select a season number (0 for all)",
        choices=[str(i) for i in range(len(seasons) + 1)],
        default="0"
    )
    
    if int(choice) == 0:
        return None
    
    selected_season = seasons[int(choice) - 1]
    return int(os.path.basename(selected_season).replace("Season ", ""))


@logger.catch
def main():
    """
    Entry point of the application with enhanced user interface.
    """
    print_welcome_message()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Automatically match and rename your MKV TV episodes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
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
        help="Specify the season number to be processed (default: all seasons)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't rename any files, just show what would happen",
    )
    parser.add_argument(
        "--get-subs",
        action="store_true",
        help="Download subtitles for the show",
    )
    parser.add_argument(
        "--check-gpu",
        action="store_true",
        help="Check if GPU is available for faster processing",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="Set confidence threshold for episode matching (0.0-1.0)",
    )
    
    args = parser.parse_args()
    if args.verbose:
        console.print("[bold cyan]Command-line Arguments[/bold cyan]")
        console.print(args)
    if args.check_gpu:
        from mkv_episode_matcher.utils import check_gpu_support
        with console.status("[bold green]Checking GPU support..."):
            check_gpu_support()
        return

    
    logger.debug(f"Command-line arguments: {args}")

    # Load configuration once
    config = get_config(CONFIG_FILE)

    # Get TMDb API key
    tmdb_api_key = args.tmdb_api_key or config.get("tmdb_api_key")

    open_subtitles_api_key = config.get("open_subtitles_api_key")
    open_subtitles_user_agent = config.get("open_subtitles_user_agent")
    open_subtitles_username = config.get("open_subtitles_username")
    open_subtitles_password = config.get("open_subtitles_password")

    if args.get_subs:
        console.print("[bold cyan]Subtitle Download Configuration[/bold cyan]")
        
        tmdb_api_key = confirm_api_key(
            tmdb_api_key, 
            "TMDb API key", 
            "Used to lookup show and episode information"
        )
        
        open_subtitles_api_key = confirm_api_key(
            open_subtitles_api_key,
            "OpenSubtitles API key",
            "Required for subtitle downloads"
        )
        
        open_subtitles_user_agent = confirm_api_key(
            open_subtitles_user_agent,
            "OpenSubtitles User Agent",
            "Required for subtitle downloads"
        )
        
        open_subtitles_username = confirm_api_key(
            open_subtitles_username,
            "OpenSubtitles Username",
            "Account username for OpenSubtitles"
        )
        
        open_subtitles_password = confirm_api_key(
            open_subtitles_password,
            "OpenSubtitles Password",
            "Account password for OpenSubtitles"
        )

    # Use config for show directory
    show_dir = args.show_dir or config.get("show_dir")
    if not show_dir:
        show_dir = Prompt.ask("Enter the main directory of the show")
    
    logger.info(f"Show Directory: {show_dir}")
    if not os.path.exists(show_dir):
        console.print(f"[bold red]Error:[/bold red] Show directory '{show_dir}' does not exist.")
        return
    
    if not show_dir:
        show_dir = os.getcwd()
        console.print(f"Using current directory: [cyan]{show_dir}[/cyan]")

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
    from mkv_episode_matcher.utils import get_valid_seasons

    console.print()
    if args.dry_run:
        console.print(
            Panel.fit(
                "[bold yellow]DRY RUN MODE[/bold yellow]\n"
                "Files will not be renamed, only showing what would happen.",
                border_style="yellow",
            )
        )
    
    seasons = get_valid_seasons(show_dir)
    if not seasons:
        console.print("[bold red]Error:[/bold red] No seasons with .mkv files found in the show directory.")
        return
    
    # If season wasn't specified and there are multiple seasons, let user choose
    selected_season = args.season
    if selected_season is None and len(seasons) > 1:
        selected_season = select_season(seasons)
    
    # Show what's going to happen
    show_name = os.path.basename(show_dir)
    season_text = f"Season {selected_season}" if selected_season else "all seasons"
    
    console.print(
        f"[bold green]Processing[/bold green] [cyan]{show_name}[/cyan], {season_text}"
    )
    
    # # Setup progress spinner
    # with Progress(
    #     TextColumn("[bold green]Processing...[/bold green]"),
    #     console=console,
    # ) as progress:
    #     task = progress.add_task("", total=None)
    process_show(
        selected_season, 
        dry_run=args.dry_run, 
        get_subs=args.get_subs, 
        verbose=args.verbose,
        confidence=args.confidence
    )
    
    console.print("[bold green]✓[/bold green] Processing completed successfully!")
    
    # Show where logs are stored
    console.print(f"\n[dim]Logs available at: {log_dir}[/dim]")


# Run the main function if the script is run directly
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        logger.exception("Unhandled exception")
        sys.exit(1)