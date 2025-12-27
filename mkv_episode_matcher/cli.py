"""
Unified CLI Interface for MKV Episode Matcher V2

This module provides a single, intuitive command-line interface that handles
all use cases with intelligent auto-detection and minimal configuration.
"""

import json
import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

from rich.table import Table

from mkv_episode_matcher.core.config_manager import get_config_manager
from mkv_episode_matcher.core.engine import MatchEngineV2
from mkv_episode_matcher.core.models import Config

app = typer.Typer(
    name="mkv-match",
    help="MKV Episode Matcher - Intelligent TV episode identification and renaming",
    no_args_is_help=True,
)

console = Console()


def print_banner():
    """Print application banner."""
    banner = Text("MKV Episode Matcher", style="bold blue")
    console.print(
        Panel(banner, subtitle="Intelligent episode matching with zero-config setup")
    )


@app.command()
def match(
    path: Path = typer.Argument(
        ..., help="Path to MKV file, series folder, or entire library", exists=True
    ),
    # Core options
    season: int | None = typer.Option(
        None, "--season", "-s", help="Override season number for all files"
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive",
        "-r/-nr",
        help="Search recursively in directories",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Preview changes without renaming files"
    ),
    # Output options
    output_dir: Path | None = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Copy renamed files to this directory instead of renaming in place",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results in JSON format for automation"
    ),
    # Quality options
    confidence_threshold: float | None = typer.Option(
        None,
        "--confidence",
        "-c",
        min=0.0,
        max=1.0,
        help="Minimum confidence score for matches (0.0-1.0)",
    ),
    # Subtitle options
    download_subs: bool = typer.Option(
        True,
        "--download-subs/--no-download-subs",
        help="Automatically download subtitles if not found locally",
    ),
):
    """
    Process MKV files with intelligent episode matching.

    Automatically detects whether you're processing:
    • A single file
    • A series folder
    • An entire library

    Examples:

        # Process a single file
        mkv-match episode.mkv

        # Process a series season
        mkv-match "/media/Breaking Bad/Season 1/"

        # Process entire library
        mkv-match /media/tv-shows/ --recursive

        # Dry run with custom output
        mkv-match episode.mkv --dry-run --output-dir ./renamed/

        # Automation mode
        mkv-match show/ --json --confidence 0.8
    """

    if not json_output:
        print_banner()

    # Load configuration
    try:
        cm = get_config_manager()
        config = cm.load()

        # Override config with CLI options
        if confidence_threshold is not None:
            config.min_confidence = confidence_threshold

        if not download_subs:
            config.sub_provider = "local"

    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Configuration error: {e}"}))
        else:
            console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)

    # Initialize engine
    try:
        engine = MatchEngineV2(config)
    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Engine initialization failed: {e}"}))
        else:
            console.print(f"[red]Failed to initialize engine: {e}[/red]")
        sys.exit(1)

    # Detect processing mode
    if path.is_file():
        mode = "single_file"
    elif path.is_dir():
        # Count MKV files to determine if it's a series or library
        mkv_count = len(list(path.rglob("*.mkv") if recursive else path.glob("*.mkv")))
        if mkv_count == 0:
            if json_output:
                print(json.dumps({"error": "No MKV files found"}))
            else:
                console.print("[yellow]No MKV files found[/yellow]")
            sys.exit(0)
        elif mkv_count <= 30:  # Arbitrary threshold
            mode = "series_folder"
        else:
            mode = "library"
    else:
        if json_output:
            print(json.dumps({"error": "Invalid path"}))
        else:
            console.print("[red]Invalid path[/red]")
        sys.exit(1)

    if not json_output:
        mode_descriptions = {
            "single_file": "Processing single file",
            "series_folder": "Processing series folder",
            "library": "Processing entire library",
        }
        console.print(f"[blue]{mode_descriptions[mode]}[/blue]: {path}")

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be renamed[/yellow]")

    # Process files
    try:
        results, failures = engine.process_path(
            path=path,
            season_override=season,
            recursive=recursive,
            dry_run=dry_run,
            output_dir=output_dir,
            json_output=json_output,
            confidence_threshold=confidence_threshold,
        )

        # Output results
        if json_output:
            output_data = {
                "mode": mode,
                "path": str(path),
                "total_matches": len(results),
                "total_failures": len(failures),
                "dry_run": dry_run,
                "results": json.loads(engine.export_results(results)),
                "failures": [
                    {
                        "original_file": str(f.original_file),
                        "reason": f.reason,
                        "confidence": f.confidence,
                    }
                    for f in failures
                ],
            }
            print(json.dumps(output_data, indent=2))
        else:
            # Rich console summary
            if results or failures:
                _display_comprehensive_summary(
                    results, failures, dry_run, output_dir, console
                )
            else:
                console.print("[yellow]No MKV files processed[/yellow]")

    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Processing failed: {e}"}))
        else:
            console.print(f"[red]Processing failed: {e}[/red]")
        sys.exit(1)


@app.command()
def config(
    show_cache_dir: bool = typer.Option(
        False, "--show-cache-dir", help="Show current cache directory location"
    ),
    reset: bool = typer.Option(
        False, "--reset", help="Reset configuration to defaults"
    ),
):
    """
    Configure MKV Episode Matcher settings.

    Most settings are auto-configured, but you can customize:
    • Cache directory location
    • Default confidence thresholds
    • ASR model preferences
    """

    cm = get_config_manager()

    if show_cache_dir:
        config = cm.load()
        console.print(f"Cache directory: [blue]{config.cache_dir}[/blue]")
        return

    if reset:
        config = Config()  # Default config
        cm.save(config)
        console.print("[green]Configuration reset to defaults[/green]")
        return

    # Interactive configuration
    console.print(Panel("MKV Episode Matcher Configuration"))

    config = cm.load()

    # Cache directory
    current_cache = str(config.cache_dir)
    new_cache = typer.prompt(
        "Cache directory", default=current_cache, show_default=True
    )
    if new_cache != current_cache:
        config.cache_dir = Path(new_cache)

    # Confidence threshold
    current_confidence = config.min_confidence
    new_confidence = typer.prompt(
        "Minimum confidence threshold (0.0-1.0)",
        type=float,
        default=current_confidence,
        show_default=True,
    )
    if 0.0 <= new_confidence <= 1.0:
        config.min_confidence = new_confidence

    # ASR provider
    current_asr = config.asr_provider
    new_asr = typer.prompt(
        "ASR provider (parakeet)",
        default=current_asr,
        show_default=True,
    )
    if new_asr in ["parakeet"]:
        config.asr_provider = new_asr

    # Subtitle provider
    current_sub = config.sub_provider
    new_sub = typer.prompt(
        "Subtitle provider (local/opensubtitles)",
        default=current_sub,
        show_default=True,
    )
    if new_sub in ["local", "opensubtitles"]:
        config.sub_provider = new_sub

    # OpenSubtitles config
    if config.sub_provider == "opensubtitles":
        console.print("\n[bold]OpenSubtitles Configuration:[/bold]")

        current_api = config.open_subtitles_api_key or ""
        new_api = typer.prompt("API Key", default=current_api, show_default=True)
        if new_api.strip():
            config.open_subtitles_api_key = new_api.strip()

        current_user = config.open_subtitles_username or ""
        new_user = typer.prompt("Username", default=current_user, show_default=True)
        if new_user.strip():
            config.open_subtitles_username = new_user.strip()

        current_pass = config.open_subtitles_password or ""
        new_pass = typer.prompt(
            "Password", default=current_pass, show_default=False, hide_input=True
        )
        if new_pass.strip():
            config.open_subtitles_password = new_pass.strip()

    # TMDB API key (optional)
    current_tmdb = config.tmdb_api_key or ""
    new_tmdb = typer.prompt(
        "TMDb API key (optional, for episode titles)",
        default=current_tmdb,
        show_default=False,
    )
    if new_tmdb.strip():
        config.tmdb_api_key = new_tmdb.strip()

    # Save configuration
    cm.save(config)
    console.print("[green]Configuration saved successfully[/green]")


@app.command()
def info():
    """
    Show system information and available models.
    """
    console.print(Panel("MKV Episode Matcher - System Information"))

    try:
        from mkv_episode_matcher.asr_models import list_available_models

        models = list_available_models()

        console.print("\n[bold]Available ASR Models:[/bold]")
        for model_type, info in models.items():
            if info.get("available"):
                status = "[green]Available[/green]"
                model_list = ", ".join(info.get("models", [])[:3])  # Show first 3
                console.print(f"  {model_type}: {status}")
                console.print(f"    Models: {model_list}")
            else:
                status = "[red]Not available[/red]"
                error = info.get("error", "Unknown error")
                console.print(f"  {model_type}: {status} ({error})")

    except Exception as e:
        console.print(f"[red]Error checking models: {e}[/red]")

    # Configuration info
    try:
        cm = get_config_manager()
        config = cm.load()

        console.print("\n[bold]Current Configuration:[/bold]")
        console.print(f"  Cache directory: {config.cache_dir}")
        console.print(f"  ASR provider: {config.asr_provider}")
        console.print(f"  Subtitle provider: {config.sub_provider}")
        console.print(f"  Confidence threshold: {config.min_confidence}")

    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")


@app.command()
def version():
    """Show version information."""
    try:
        import mkv_episode_matcher

        version = mkv_episode_matcher.__version__
    except AttributeError:
        version = "unknown"

    console.print(f"MKV Episode Matcher v{version}")


def _display_comprehensive_summary(results, failures, dry_run, output_dir, console):
    """Display a comprehensive summary of matching results."""
    from collections import defaultdict

    console.print("\n[bold green]Processing Complete![/bold green]")
    console.print(f"[blue]Successfully processed {len(results)} files[/blue]")
    if failures:
        console.print(f"[red]Failed to match {len(failures)} files[/red]\n")
    else:
        console.print("\n")

    # Group results by series/season for organized display
    series_groups = defaultdict(lambda: defaultdict(list))
    total_confidence = 0

    for result in results:
        series_name = result.episode_info.series_name
        season = result.episode_info.season
        series_groups[series_name][season].append(result)
        total_confidence += result.confidence

    # Create summary table
    table = Table(title="Episode Matching Summary")
    table.add_column("Original File", style="cyan")
    table.add_column("New Name", style="green")
    table.add_column("Episode", style="magenta", justify="center")
    table.add_column("Confidence", style="yellow", justify="center")
    table.add_column("Status", style="white", justify="center")

    for series_name in sorted(series_groups.keys()):
        for season in sorted(series_groups[series_name].keys()):
            episodes = series_groups[series_name][season]

            # Add series header if multiple series
            if len(series_groups) > 1:
                table.add_row(
                    f"[bold cyan]{series_name} - Season {season}[/bold cyan]",
                    "",
                    "",
                    "",
                    "",
                    style="bold cyan",
                )

            for result in sorted(episodes, key=lambda x: x.episode_info.episode):
                # Use original filename if available, otherwise current filename
                original_name = (
                    result.original_file.name
                    if result.original_file
                    else result.matched_file.name
                )

                # Generate expected new name
                title_part = (
                    f" - {result.episode_info.title}"
                    if result.episode_info.title
                    else ""
                )
                new_name = f"{result.episode_info.series_name} - {result.episode_info.s_e_format}{title_part}{result.matched_file.suffix}"

                # Clean the new name for display
                import re

                new_name = re.sub(r'[<>:"/\\\\|?*]', "", new_name).strip()

                status = (
                    "WOULD RENAME"
                    if dry_run
                    else (
                        "RENAMED"
                        if (
                            result.original_file
                            and result.original_file.name != result.matched_file.name
                        )
                        else "COPY"
                        if output_dir
                        else "RENAMED"
                    )
                )

                table.add_row(
                    original_name,
                    new_name,
                    result.episode_info.s_e_format,
                    f"{result.confidence:.2f}",
                    status,
                )

    # Add failures to table if any
    if failures:
        for failure in failures:
            table.add_row(
                failure.original_file.name,
                "-",
                "-",
                f"{failure.confidence:.2f}" if failure.confidence > 0 else "-",
                "[red]FAILED[/red]",
            )

    console.print(table)

    # Display summary statistics
    avg_confidence = total_confidence / len(results) if results else 0
    console.print("\n[bold]Summary Statistics:[/bold]")
    console.print(f"  Total episodes matched: [green]{len(results)}[/green]")
    if failures:
        console.print(f"  Total failures: [red]{len(failures)}[/red]")
    console.print(
        f"  Average confidence (matches): [yellow]{avg_confidence:.2f}[/yellow]"
    )
    console.print(f"  Series processed: [blue]{len(series_groups)}[/blue]")

    # Season breakdown
    season_count = sum(len(seasons) for seasons in series_groups.values())
    console.print(f"  Seasons processed: [magenta]{season_count}[/magenta]")

    # Display action taken
    console.print("\n[bold]Action Taken:[/bold]")
    if dry_run:
        console.print("[yellow]DRY RUN - No files were actually renamed[/yellow]")
        console.print(
            "Run the command without [bold]--dry-run[/bold] to perform the renames"
        )
    elif output_dir:
        console.print(f"[blue]Files copied to: {output_dir}[/blue]")
        console.print("Original files remain unchanged")
    else:
        console.print("[green]Files renamed in place[/green]")
        console.print("Original filenames have been updated")

    # Show command to view renamed files
    if not dry_run:
        if output_dir:
            console.print(f'\n[dim]View results: ls "{output_dir}"[/dim]')
        else:
            # Get the parent directory of the first result for the ls command
            if results:
                first_file_dir = results[0].matched_file.parent
                console.print(f'\n[dim]View results: ls "{first_file_dir}"[/dim]')

    # Warning for failures
    if failures:
        console.print("\n[bold red]Warnings:[/bold red]")
        console.print(
            f"[yellow]  • {len(failures)} files could not be matched.[/yellow]"
        )
        console.print("  • Try checking if correct subtitles are available online.")
        console.print(
            "  • Consider lowering the confidence threshold with [bold]--confidence[/bold] if matches are close."
        )


@app.command()
def gui():
    """Launch the GUI application."""
    import flet as ft

    from mkv_episode_matcher.ui.flet_app import main

    ft.app(target=main)


if __name__ == "__main__":
    app()
