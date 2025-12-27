#!/usr/bin/env python3
"""
Debug script specifically for Parakeet transcription issues.
"""

import sys
import time
from pathlib import Path

import torch
from loguru import logger

# Add parent directory to path to import the modules
sys.path.append(str(Path(__file__).parent.parent))
from mkv_episode_matcher.asr_models import create_asr_model


def debug_parakeet_transcription():
    """Debug parakeet transcription in detail."""

    # Configure logger to show debug messages
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    print("=== Parakeet Debug Session ===")
    print(f"CUDA Available: {torch.cuda.is_available()}")

    # Use the same audio file that was extracted in diagnostics
    audio_file = r"C:\Users\Jonathan\AppData\Local\Temp\whisper_chunks\chunk_300.wav"

    if not Path(audio_file).exists():
        print(f"ERROR: Audio file not found: {audio_file}")
        print("Please run the diagnostic test first to extract audio chunks")
        return

    print(f"Testing audio file: {audio_file}")
    print(f"Audio file size: {Path(audio_file).stat().st_size} bytes")

    # Test parakeet models
    configs = [
        {"type": "parakeet", "name": "nvidia/parakeet-tdt-0.6b-v2", "device": "cpu"},
        {"type": "parakeet", "name": "nvidia/parakeet-tdt-0.6b-v2", "device": "cuda"},
    ]

    for config in configs:
        print(f"\n--- Testing {config['type']} on {config['device']} ---")

        try:
            # Create and load model
            print("Creating model...")
            model = create_asr_model(config)

            print("Loading model...")
            start_load = time.time()
            model.load()
            load_time = time.time() - start_load
            print(f"Model loaded in {load_time:.2f}s")

            # Test transcription with detailed debugging
            print("Starting transcription...")
            start_time = time.time()

            # Call transcribe method directly to see what happens
            result = model.transcribe(audio_file)

            transcription_time = time.time() - start_time

            print(f"Transcription completed in {transcription_time:.2f}s")
            print(f"Result type: {type(result)}")
            print(
                f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
            )
            print(f"Raw text: '{result.get('raw_text', 'N/A')}'")
            print(f"Cleaned text: '{result.get('text', 'N/A')}'")
            print(f"Text length: {len(result.get('text', ''))}")

            if "segments" in result:
                print(f"Segments: {len(result['segments'])}")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    debug_parakeet_transcription()
