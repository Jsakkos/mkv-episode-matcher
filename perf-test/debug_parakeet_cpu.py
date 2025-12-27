import sys
import time
from pathlib import Path

from rich import print

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from mkv_episode_matcher.asr_models import ParakeetASRModel


def debug_cpu():
    print("[bold]Testing Parakeet on CPU...[/bold]")

    test_file = Path(__file__).parent / "debug_audio" / "extracted_chunk.wav"
    if not test_file.exists():
        print(
            "[red]extracted_chunk.wav not found, run debug_audio_processing.py first[/red]"
        )
        return

    try:
        model = ParakeetASRModel(device="cpu")
        print("Loading model on CPU...")
        start = time.time()
        model.load()
        print(f"Loaded in {time.time() - start:.2f}s")

        print(f"Transcribing {test_file}...")
        start = time.time()
        result = model.transcribe(test_file)
        duration = time.time() - start

        print(f"Transcription took {duration:.2f}s")
        print(f"Text: '{result['text']}'")

        if result["text"]:
            print("[green]CPU Transcription SUCCESS[/green]")
        else:
            print("[red]CPU Transcription returned empty string[/red]")

    except Exception as e:
        print(f"[red]Failed: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_cpu()
