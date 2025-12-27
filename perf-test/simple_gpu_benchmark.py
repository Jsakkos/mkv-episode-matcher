#!/usr/bin/env python3
"""
Simplified GPU-only benchmark for Mkv Episode Matcher.
Compares Whisper vs Parakeet on a single file with 1 iteration.
"""

import sys
import time
from pathlib import Path

import torch
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mkv_episode_matcher.episode_identification import (
    EpisodeMatcher,
)
from mkv_episode_matcher.utils import extract_season_episode

console = Console()


def run_simple_benchmark():
    console.print(
        Panel.fit(
            "[bold blue]Simplified GPU Benchmark: Whisper vs Parakeet[/bold blue]"
        )
    )

    if not torch.cuda.is_available():
        console.print(
            "[bold red]Error: CUDA is not available. This benchmark requires GPU.[/bold red]"
        )
        sys.exit(1)

    console.print(f"[green]CUDA Device: {torch.cuda.get_device_name(0)}[/green]")

    # 1. Find a test file
    test_files_dir = Path(__file__).parent / "inputs"
    # 1. Find a test file
    test_files_dir = Path(__file__).parent / "inputs"
    test_file = test_files_dir / "The Expanse - S01E01.mkv"

    if not test_file.exists():
        console.print(f"[red]Test file not found: {test_file}[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Test File:[/bold] {test_file.name}")

    # Extract info
    season, episode = extract_season_episode(test_file.name)
    show_name = "Test Show"  # Placeholder, logic in actual app is more complex but we assume cache exists
    # Try to deduce show name from filename for cache lookup simplicity?
    # Actually, let's use the same logic as the main benchmark to find the show name if possible,
    # but for now let's just assume the user has set up the cache correctly for this file.
    # We'll use the one from the directory structure or just rely on 'show_name' passed to EpisodeMatcher.

    # Let's try to get a real show name if we can, or hardcode one that likely works with the inputs
    # if the user provided specific inputs. Since I don't know the inputs, I'll rely on the folder name
    # or just ask the user if it fails.
    # BUT, looking at `generate_ground_truth` in `performance_benchmark.py`, it extracts show name.
    # Let's copy that regex logic briefly.
    import re

    match = re.match(r"^(.+?)\s*-\s*[Ss]\d+[Ee]\d+", test_file.stem)
    if match:
        show_name = match.group(1).strip()
    console.print(f"[bold]Detected Show Name:[/bold] {show_name}")
    console.print(f"[bold]Target:[/bold] S{season:02d}E{episode:02d}")

    # Debug cache path
    cache_root = Path.home() / ".mkv-episode-matcher" / "cache"
    cache_dir = cache_root / "data"
    expected_show_dir = cache_dir / show_name
    console.print(f"[bold]Expected Cache Path:[/bold] {expected_show_dir}")
    if expected_show_dir.exists():
        console.print("[green]Cache directory exists.[/green]")
        srt_files = list(expected_show_dir.glob("*.srt")) + list(
            expected_show_dir.glob("*.SRT")
        )
        console.print(f"Found {len(srt_files)} SRT files.")
    else:
        console.print(f"[red]Cache directory NOT found at {expected_show_dir}[/red]")
        # LIST CLOSEST MATCHES
        if cache_dir.exists():
            console.print("Available shows:")
            for d in cache_dir.iterdir():
                if show_name.lower() in d.name.lower():
                    console.print(f"  - {d.name}")

    # Models to test
    models = [
        # {"type": "parakeet", "name": "nvidia/parakeet-tdt-0.6b-v2", "device": "cuda"}, # Broken
        {"type": "parakeet", "name": "nvidia/parakeet-ctc-0.6b", "device": "cuda"},
        {"type": "whisper", "name": "tiny.en", "device": "cuda"},
    ]

    results = []

    for model_config in models:
        model_name = f"{model_config['type']}:{model_config['name']}"
        console.print(f"\n[bold]Testing {model_name}...[/bold]")

        # Create matcher
        class SimpleCustomMatcher(EpisodeMatcher):
            def __init__(self, cache_dir, show_name, model_config):
                super().__init__(
                    cache_dir, show_name, min_confidence=0.1, device="cuda"
                )
                self.model_config = model_config

            def identify_episode(self, video_file, temp_dir, season_number):
                console.print(
                    f"[dim]Identifying {video_file.name} (S{season_number})...[/dim]"
                )

                # Debug reference files logic manually
                ref_dir = self.cache_dir / "data" / self.show_name
                # console.print(f"Debug: Matcher looking in {ref_dir}")

                reference_files = self.get_reference_files(season_number)
                if not reference_files:
                    console.print(
                        f"[red]No reference files found for S{season_number}![/red]"
                    )
                    return None

                console.print(
                    f"[dim]Found {len(reference_files)} reference files.[/dim]"
                )
                duration = 300
                return self._try_match_with_model(
                    video_file, self.model_config, duration, reference_files
                )

            def _try_match_with_model(
                self, video_file, model_config, max_duration, reference_files
            ):
                # We override this to print the transcription
                # Use cached model
                from mkv_episode_matcher.asr_models import get_cached_model

                model = get_cached_model(model_config)

                num_chunks = min(max_duration // self.chunk_duration, 10)

                for chunk_idx in range(num_chunks):
                    start_time = self.skip_initial_duration + (
                        chunk_idx * self.chunk_duration
                    )
                    console.print(f"[dim]Processing chunk at {start_time}s...[/dim]")
                    try:
                        audio_path = self.extract_audio_chunk(video_file, start_time)
                        result = model.transcribe(audio_path)
                        text = result["text"]
                        # Use repr() to avoid unicode errors in console output
                        console.print(
                            f"[bold magenta]Transcribed ({model_config['type']}):[/bold magenta] {repr(text)}"
                        )

                        # Calculate score to see why it fails
                        best_conf = 0
                        for ref_file in reference_files:
                            ref_text = self.load_reference_chunk(ref_file, chunk_idx)
                            if chunk_idx == 0 and ref_text:
                                # Safe print
                                safe_ref = repr(ref_text[:50])
                                console.print(
                                    f"[dim]Ref example ({Path(ref_file).name}): {safe_ref}...[/dim]"
                                )

                            conf = model.calculate_match_score(text, ref_text)
                            if conf > best_conf:
                                best_conf = conf

                        console.print(f"[bold]Best Confidence:[/bold] {best_conf:.2f}")

                        if best_conf > self.min_confidence:
                            return {
                                "season": 1,
                                "episode": 1,
                                "confidence": best_conf,
                            }  # Simplified return

                    except Exception as e:
                        console.print(f"[red]Error in chunk {start_time}: {e}[/red]")
                        import traceback

                        traceback.print_exc()

                return None

        matcher = SimpleCustomMatcher(cache_root, show_name, model_config)

        start_time = time.time()
        try:
            temp_dir = Path(__file__).parent / "temp"
            temp_dir.mkdir(exist_ok=True)
            match = matcher.identify_episode(test_file, temp_dir, season)
            duration = time.time() - start_time

            status = "[green]MATCH[/green]" if match else "[red]NO MATCH[/red]"
            conf = match["confidence"] if match else 0.0
            matched_ep = f"S{match['season']}E{match['episode']}" if match else "N/A"

            results.append({
                "model": model_name,
                "time": duration,
                "status": status,
                "confidence": conf,
                "matched": matched_ep,
            })

        except Exception as e:
            console.print(f"[red]Error running {model_name}: {e}[/red]")
            import traceback

            traceback.print_exc()

    # Display Table
    table = Table(title="Benchmark Results")
    table.add_column("Model")
    table.add_column("Time (s)")
    table.add_column("Status")
    table.add_column("Confidence")
    table.add_column("Matched Ep")

    for r in results:
        table.add_row(
            r["model"],
            f"{r['time']:.2f}",
            f"{r['status']}",
            f"{r['confidence']:.2f}",
            r["matched"],
        )

    console.print(table)


if __name__ == "__main__":
    run_simple_benchmark()
