# mkv_episode_matcher/episode_matcher.py

import re
import shutil
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from mkv_episode_matcher.__main__ import CACHE_DIR, CONFIG_FILE
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.episode_identification import EpisodeMatcher
from mkv_episode_matcher.tmdb_client import fetch_show_id
from mkv_episode_matcher.utils import (
    check_filename,
    clean_text,
    get_subtitles,
    get_valid_seasons,
    normalize_path,
    rename_episode_file,
)

# Initialize Rich console
console = Console()


def process_show(
    season=None, dry_run=False, get_subs=False, verbose=False, confidence=0.6
):
    """
    Process the show using streaming speech recognition with improved UI feedback.

    Args:
        season (int, optional): Season number to process. Defaults to None (all seasons).
        dry_run (bool): If True, only simulate actions without making changes.
        get_subs (bool): If True, download subtitles for the show.
        verbose (bool): If True, display more detailed progress information.
        confidence (float): Confidence threshold for episode matching (0.0-1.0).
    """
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = clean_text(normalize_path(show_dir).name)
    matcher = EpisodeMatcher(CACHE_DIR, show_name, min_confidence=confidence)

    # Early check for reference files
    reference_dir = Path(CACHE_DIR) / "data" / show_name
    reference_files = list(reference_dir.glob("*.srt"))
    if (not get_subs) and (not reference_files):
        console.print(
            f"[bold yellow]Warning:[/bold yellow] No reference subtitle files found in {reference_dir}"
        )
        console.print(
            "[cyan]Tip:[/cyan] Use --get-subs to download reference subtitles"
        )
        return

    season_paths = get_valid_seasons(show_dir)
    if not season_paths:
        console.print("[bold red]Error:[/bold red] No seasons with .mkv files found")
        return

    if season is not None:
        season_path = str(Path(show_dir) / f"Season {season}")
        if season_path not in season_paths:
            console.print(
                f"[bold red]Error:[/bold red] Season {season} has no .mkv files to process"
            )
            return
        season_paths = [season_path]

    total_processed = 0
    total_matched = 0

    for season_path in season_paths:
        mkv_files = [
            f for f in Path(season_path).glob("*.mkv") if not check_filename(f)
        ]

        if not mkv_files:
            season_num = Path(season_path).name.replace("Season ", "")
            console.print(f"[dim]No new files to process in Season {season_num}[/dim]")
            continue

        season_num = int(re.search(r"Season (\d+)", season_path).group(1))
        temp_dir = Path(season_path) / "temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            if get_subs:
                show_id = fetch_show_id(matcher.show_name)
                if show_id:
                    console.print(
                        f"[bold cyan]Downloading subtitles for Season {season_num}...[/bold cyan]"
                    )
                    get_subtitles(show_id, seasons={season_num}, config=config)
                else:
                    console.print(
                        "[bold red]Error:[/bold red] Could not find show ID. Skipping subtitle download."
                    )

            console.print(
                f"[bold cyan]Processing {len(mkv_files)} files in Season {season_num}...[/bold cyan]"
            )

            # Process files with a progress bar
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Matching Season {season_num}[/cyan]", total=len(mkv_files)
                )

                for mkv_file in mkv_files:
                    file_basename = Path(mkv_file).name
                    progress.update(
                        task, description=f"[cyan]Processing[/cyan] {file_basename}"
                    )

                    if verbose:
                        console.print(f"  Analyzing {file_basename}...")

                    total_processed += 1
                    match = matcher.identify_episode(mkv_file, temp_dir, season_num)

                    if match:
                        total_matched += 1
                        new_name = f"{matcher.show_name} - S{match['season']:02d}E{match['episode']:02d}.mkv"

                        confidence_color = (
                            "green" if match["confidence"] > 0.8 else "yellow"
                        )

                        if verbose or dry_run:
                            console.print(
                                f"  Match: [bold]{file_basename}[/bold] → [bold cyan]{new_name}[/bold cyan] "
                                f"(confidence: [{confidence_color}]{match['confidence']:.2f}[/{confidence_color}])"
                            )

                        if not dry_run:
                            rename_episode_file(mkv_file, new_name)
                    else:
                        if verbose:
                            console.print(
                                f"  [yellow]No match found for {file_basename}[/yellow]"
                            )

                    progress.advance(task)
        finally:
            if not dry_run and temp_dir.exists():
                shutil.rmtree(temp_dir)

    # Summary
    console.print()
    if total_processed == 0:
        console.print("[yellow]No files needed processing[/yellow]")
    else:
        console.print(f"[bold]Summary:[/bold] Processed {total_processed} files")
        console.print(
            f"[bold green]Successfully matched:[/bold green] {total_matched} files"
        )

        if total_matched < total_processed:
            console.print(
                f"[bold yellow]Unmatched:[/bold yellow] {total_processed - total_matched} files"
            )
            console.print(
                "[cyan]Tip:[/cyan] Try downloading subtitles with --get-subs or "
                "check that your files are named consistently"
            )
