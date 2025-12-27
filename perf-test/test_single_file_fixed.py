#!/usr/bin/env python3
"""
Quick test to verify the cache directory path fix works.
Tests just one file to check if reference subtitles are found.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from mkv_episode_matcher.episode_identification import EpisodeMatcher


# Test the path resolution fix
def test_path_fix():
    print("Testing cache directory path resolution...")

    # Load config the same way the benchmark does
    cache_dir_config = "~/.mkv-episode-matcher/cache"
    cache_dir = Path(cache_dir_config).expanduser()

    print(f"Config path: {cache_dir_config}")
    print(f"Expanded path: {cache_dir}")
    print(f"Cache dir exists: {cache_dir.exists()}")

    if cache_dir.exists():
        data_dir = cache_dir / "data"
        print(f"Data dir: {data_dir}")
        print(f"Data dir exists: {data_dir.exists()}")

        if data_dir.exists():
            show_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
            print(f"Found {len(show_dirs)} show directories:")
            for show_dir in show_dirs[:5]:  # Show first 5
                srt_files = list(show_dir.glob("*.srt"))
                print(f"  {show_dir.name}: {len(srt_files)} subtitle files")

    # Test with House of the Dragon
    print("\nTesting House of the Dragon subtitle lookup...")
    show_name = "House of the Dragon"
    season = 1

    matcher = EpisodeMatcher(cache_dir, show_name, min_confidence=0.6)
    reference_files = matcher.get_reference_files(season)

    print(
        f"Found {len(reference_files)} reference files for {show_name} Season {season}"
    )
    for ref_file in reference_files[:3]:  # Show first 3
        print(f"  - {ref_file}")

    return len(reference_files) > 0


if __name__ == "__main__":
    success = test_path_fix()
    if success:
        print("\n✓ SUCCESS: Reference files found! Path fix works.")
    else:
        print("\n✗ FAILED: No reference files found.")
