# __main__.py (enhanced version)
import argparse
import sys
from pathlib import Path
from typing import Optional

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from mkv_episode_matcher import __version__
from mkv_episode_matcher.config import get_config, set_config

# Initialize rich console for better output
console = Console()

# Log the start of the application
logger.info("Starting the application")

# Check if the configuration directory exists, if not create it
CONFIG_DIR = Path.home() / ".mkv-episode-matcher"
if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Define the paths for the configuration file and cache directory
CONFIG_FILE = CONFIG_DIR / "config.ini"
CACHE_DIR = CONFIG_DIR / "cache"

# Check if the cache directory exists, if not create it
if not CACHE_DIR.exists():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Check if logs directory exists, if not create it
log_dir = CONFIG_DIR / "logs"
if not log_dir.exists():
    log_dir.mkdir(exist_ok=True)
logger.remove()
# Add a new handler for stdout logs
logger.add(
    str(log_dir / "stdout.log"),
    format="{time} {level} {message}",
    level="INFO",
    rotation="10 MB",
)

# Add a new handler for error logs
logger.add(str(log_dir / "stderr.log"), level="ERROR", rotation="10 MB")


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


def confirm_api_key(
    config_value: Optional[str], key_name: str, description: str
) -> str:
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
        season_num = Path(season).name.replace("Season ", "")
        console.print(f"  {i}. Season {season_num}")

    console.print("  0. All Seasons")

    choice = Prompt.ask(
        "Select a season number (0 for all)",
        choices=[str(i) for i in range(len(seasons) + 1)],
        default="0",
    )

    if int(choice) == 0:
        return None

    selected_season = seasons[int(choice) - 1]
    return int(Path(selected_season).name.replace("Season ", ""))

def onboarding(config_path):
    """Prompt user for all required config values, showing existing as defaults."""
    config = get_config(config_path) if config_path.exists() else {}

    def ask_with_default(prompt_text, key, description, secret=False):
        current = config.get(key)
        if current:
            console.print(f"[cyan]{key}:[/cyan] {description}")
            console.print(f"Current value: [green]{mask_api_key(current) if secret else current}[/green]")
            if Confirm.ask("Use existing value?", default=True):
                return current
        return Prompt.ask(f"Enter your {key}", default=current or "")

    tmdb_api_key = ask_with_default("TMDb API key", "tmdb_api_key", "Used to lookup show and episode information. To get your API key, create an account at https://www.themoviedb.org/ and follow the instructions at https://developer.themoviedb.org/docs/getting-started", secret=True)
    open_subtitles_username = ask_with_default("OpenSubtitles Username", "open_subtitles_username", "Account username for OpenSubtitles. To create an account, visit https://www.opensubtitles.com/ then click 'Register'")
    open_subtitles_password = ask_with_default("OpenSubtitles Password", "open_subtitles_password", "Account password for OpenSubtitles", secret=True)
    open_subtitles_user_agent = ask_with_default("OpenSubtitles Consumer Name", "open_subtitles_user_agent", "Required for subtitle downloads. Go to https://www.opensubtitles.com/en/consumers, click 'New Consumer', give it a name, then click 'Save'")
    open_subtitles_api_key = ask_with_default("OpenSubtitles API key", "open_subtitles_api_key", "Required for subtitle downloads. Enter the API key linked with the OpenSubtitles Consumer that you created in the previous step.", secret=True)
    show_dir = ask_with_default("Show Directory", "show_dir", "Main directory of the show")

    set_config(
        tmdb_api_key,
        open_subtitles_api_key,
        open_subtitles_user_agent,
        open_subtitles_username,
        open_subtitles_password,
        show_dir,
        config_path,
    )
    console.print("[bold green]Onboarding complete! Configuration saved.[/bold green]")

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
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.7,
        help="Set confidence threshold for episode matching (0.0-1.0)",
    )
    parser.add_argument(
        "--onboard",
        action="store_true",
        help="Run onboarding to set up configuration",
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
    # Onboarding: run if --onboard or config file missing
    if args.onboard or not CONFIG_FILE.exists():
        onboarding(CONFIG_FILE)
        # Reload config after onboarding
        config = get_config(CONFIG_FILE)
    else:
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
            tmdb_api_key, "TMDb API key", "Used to lookup show and episode information"
        )

        open_subtitles_api_key = confirm_api_key(
            open_subtitles_api_key,
            "OpenSubtitles API key",
            "Required for subtitle downloads",
        )

        open_subtitles_user_agent = confirm_api_key(
            open_subtitles_user_agent,
            "OpenSubtitles User Agent",
            "Required for subtitle downloads",
        )

        open_subtitles_username = confirm_api_key(
            open_subtitles_username,
            "OpenSubtitles Username",
            "Account username for OpenSubtitles",
        )

        open_subtitles_password = confirm_api_key(
            open_subtitles_password,
            "OpenSubtitles Password",
            "Account password for OpenSubtitles",
        )

    # Use config for show directory
    show_dir = args.show_dir or config.get("show_dir")
    if not show_dir:
        show_dir = Prompt.ask("Enter the main directory of the show")

    logger.info(f"Show Directory: {show_dir}")
    if not Path(show_dir).exists():
        console.print(
            f"[bold red]Error:[/bold red] Show directory '{show_dir}' does not exist."
        )
        return

    if not show_dir:
        show_dir = Path.cwd()
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
        console.print(
            "[bold red]Error:[/bold red] No seasons with .mkv files found in the show directory."
        )
        return

    # If season wasn't specified and there are multiple seasons, let user choose
    selected_season = args.season
    if selected_season is None and len(seasons) > 1:
        selected_season = select_season(seasons)

    # Show what's going to happen
    show_name = Path(show_dir).name
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
        confidence=args.confidence,
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
