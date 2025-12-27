#!/usr/bin/env python3
"""
Test single file matching to debug the benchmark issues
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from mkv_episode_matcher.episode_identification import EpisodeMatcher
from mkv_episode_matcher.utils import clean_text


def test_single_file():
    """Test matching with a single file to debug issues."""

    # Test with Rick and Morty
    show_name = "Rick and Morty"
    cleaned_show_name = clean_text(show_name)

    print(f"Original show name: {show_name}")
    print(f"Cleaned show name: {cleaned_show_name}")

    cache_dir = Path.home() / ".mkv-episode-matcher" / "cache"
    test_file = Path(__file__).parent / "inputs" / "Rick and Morty - S01E01.mkv"

    print(f"Cache directory: {cache_dir}")
    print(f"Test file: {test_file}")
    print(f"Test file exists: {test_file.exists()}")

    # Check reference directory
    ref_dir = cache_dir / "data" / cleaned_show_name
    print(f"Reference directory: {ref_dir}")
    print(f"Reference directory exists: {ref_dir.exists()}")

    if ref_dir.exists():
        ref_files = list(ref_dir.glob("*.srt"))
        print(f"Reference files found: {len(ref_files)}")
        for ref_file in ref_files[:3]:  # Show first 3
            print(f"  - {ref_file.name}")

    # Try to run the matcher
    print("\n=== Running Episode Matcher ===")
    try:
        matcher = EpisodeMatcher(cache_dir, cleaned_show_name, min_confidence=0.6)

        # Create temp directory
        temp_dir = cache_dir / "temp"
        temp_dir.mkdir(exist_ok=True)

        print("Matcher initialized successfully")
        print("Running identify_episode...")

        result = matcher.identify_episode(test_file, temp_dir, season=1)

        if result:
            print("SUCCESS: Match found!")
            print(f"  Season: {result.get('season')}")
            print(f"  Episode: {result.get('episode')}")
            print(f"  Confidence: {result.get('confidence', 0):.2f}")
            print(f"  Reference: {result.get('reference_file')}")
        else:
            print("No match found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_single_file()
