#!/usr/bin/env python3
"""
Benchmark Subtitle Cache Loading
"""

import sys
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from mkv_episode_matcher.episode_identification import EpisodeMatcher

console = Console()


def benchmark_cache_loading():
    console.print("[bold blue]Benchmark: Subtitle Cache Loading[/bold blue]")

    # Setup
    cache_root = Path.home() / ".mkv-episode-matcher" / "cache"
    # We use a dummy show name that likely exists or use 'The Expanse' if proven to exist
    show_name = "The Expanse"

    console.print(f"Target Show: {show_name}")
    console.print(f"Cache Root: {cache_root}")

    matcher = EpisodeMatcher(cache_root, show_name)

    # Measure get_reference_files (scanning directory)
    start_time = time.perf_counter()
    ref_files = matcher.get_reference_files(1)  # Season 1
    dir_scan_time = time.perf_counter() - start_time

    console.print(f"Directory Scan Time: {dir_scan_time:.4f}s")
    console.print(f"Found {len(ref_files)} reference files")

    if not ref_files:
        console.print(
            "[red]No reference files found. Skipping parsing benchmark.[/red]"
        )
        return

    # Measure parsing speed (load_reference_chunk calls get_subtitle_content which parses SRT)
    # We'll force load all of them
    start_time = time.perf_counter()
    loaded_count = 0
    total_lines = 0

    for ref_file in ref_files:
        # Accessing subtitle_cache directly to measure full parse time
        content = matcher.subtitle_cache.get_subtitle_content(ref_file)
        loaded_count += 1
        total_lines += len(content)

    parse_time = time.perf_counter() - start_time

    console.print(f"Subtitle Parse Time: {parse_time:.4f}s")
    console.print(f"Parsed {loaded_count} files, {total_lines} chunks/lines")
    console.print(f"Average time per file: {parse_time / loaded_count:.4f}s")

    # Table Results
    table = Table(title="Cache Performance")
    table.add_column("Operation")
    table.add_column("Time (s)")
    table.add_column("Items")
    table.add_column("Rate")

    table.add_row(
        "Directory Scan", f"{dir_scan_time:.4f}", f"{len(ref_files)} files", "-"
    )
    table.add_row(
        "SRT Parsing",
        f"{parse_time:.4f}",
        f"{loaded_count} files",
        f"{loaded_count / parse_time:.1f} files/s",
    )

    console.print(table)


if __name__ == "__main__":
    benchmark_cache_loading()
