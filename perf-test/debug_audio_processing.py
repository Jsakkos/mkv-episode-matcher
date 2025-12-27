import shutil
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from rich import print

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from mkv_episode_matcher.asr_models import ParakeetASRModel


def debug_preprocessing():
    test_file = Path(__file__).parent / "inputs" / "The Expanse - S01E01.mkv"
    if not test_file.exists():
        print(f"[red]Test file {test_file} not found[/red]")
        return

    work_dir = Path(__file__).parent / "debug_audio"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    # 1. Extract Chunk Manually (300s, 30s)
    print("\n[bold]1. Extracting Audio Chunk...[/bold]")
    chunk_path = work_dir / "extracted_chunk.wav"
    cmd = [
        "ffmpeg",
        "-ss",
        "300",
        "-t",
        "30",
        "-i",
        str(test_file),
        "-vn",
        "-sn",
        "-dn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-y",
        str(chunk_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Extracted to {chunk_path}")

    # Analyze Extracted Audio
    y, sr = librosa.load(str(chunk_path), sr=None)
    print(
        f"Original Audio: SR={sr}, Shape={y.shape}, Max={np.max(np.abs(y))}, Mean={np.mean(np.abs(y))}"
    )
    if np.max(np.abs(y)) == 0:
        print("[red]Original extracted audio is SILENT![/red]")
        return

    # 2. Run Preprocessing Logic
    print("\n[bold]2. Running Preprocessing...[/bold]")

    # Replica of ParakeetASRModel._preprocess_audio logic
    audio = y
    target_sr = 16000
    if sr != target_sr:
        print("Resampling...")
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)

    # Normalize
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio))
    print(
        f"After Normalize: Max={np.max(np.abs(audio))}, Mean={np.mean(np.abs(audio))}"
    )

    # Noise Reduction
    orig_non_zero = np.count_nonzero(audio)
    audio_reduced = np.where(np.abs(audio) < 0.01, 0, audio)
    new_non_zero = np.count_nonzero(audio_reduced)
    print(f"After Noise Reduction: Non-Zero Samples {orig_non_zero} -> {new_non_zero}")
    if new_non_zero == 0:
        print("[red]Noise reduction silenced the ENTIRE audio![/red]")

    preprocessed_path = work_dir / "preprocessed_debug.wav"
    sf.write(str(preprocessed_path), audio_reduced, target_sr)

    # 3. Transcribe with Parakeet
    print("\n[bold]3. Transcribing...[/bold]")
    model = ParakeetASRModel(device="cuda")
    # model.load() # Implicit

    print("Transcribing PREPROCESSED file...")
    res_prep = model.transcribe(preprocessed_path)
    print(f"Preprocessed Result: '{res_prep['text']}'")
    print(f"Preprocessed Raw: '{res_prep['raw_text']}'")

    print(
        "Transcribing ORIGINAL file (bypassing internal preprocess if possible, but transcribe calls it)..."
    )
    # We can't easily bypass _preprocess_audio inside describe without monkeypatching or calling _model.transcribe directly
    # But wait, transcribe calls _preprocess_audio.
    # Let's try calling the internal model directly to see if raw audio works

    if model.is_loaded:
        pass
    else:
        model.load()

    print("Transcribing ORIGINAL file via internal NeMo model directly...")
    # NeMo transcribe takes list of paths
    res_nemo = model._model.transcribe([str(chunk_path)])
    text_nemo = res_nemo[0] if res_nemo else ""
    # Handle list or object
    if hasattr(text_nemo, "text"):
        text_nemo = text_nemo.text
    print(f"Direct NeMo Result on Original: '{text_nemo}'")


if __name__ == "__main__":
    debug_preprocessing()
