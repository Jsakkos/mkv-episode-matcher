import subprocess
import time
from pathlib import Path

from mkv_episode_matcher.core.engine import MatchEngine
from mkv_episode_matcher.core.models import Config


def generate_dummy_mkv(path: Path, duration_sec=600):
    """Generate a dummy MKV with specific audio frequency tone to simulate speech-like audio existence."""
    # We use a sine wave at 440hz. ASR won't transcribe it as English likely, but it processes audio.
    # To test ASR speed we just need valid audio.
    if path.exists():
        return

    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration_sec}",
        "-c:a",
        "pcm_s16le",
        "-f",
        "matroska",
        "-y",
        str(path),
    ]
    subprocess.run(cmd, check=True)


def benchmark():
    base_dir = Path("perf_test_data")
    base_dir.mkdir(exist_ok=True)
    show_dir = base_dir / "TestShow"
    season_dir = show_dir / "Season 1"
    season_dir.mkdir(parents=True, exist_ok=True)

    # Create Cache dir for subtitles
    cache_dir = base_dir / "cache"
    sub_cache = cache_dir / "data" / "TestShow"
    sub_cache.mkdir(parents=True, exist_ok=True)

    # 1. Generate Video
    video_path = season_dir / "episode1.mkv"
    print("Generating dummy video...")
    generate_dummy_mkv(video_path)

    # 2. Generate Subtitle
    # We put some text that might be matched if ASR hallucinates, but mostly we test processing speed.
    # To test meaningful matching, we'd need real speech.
    # But for "Performance", we care about Extraction + Inference time.
    (sub_cache / "TestShow - S01E01.srt").write_text(
        "1\n00:00:30,000 --> 00:00:35,000\nHello world this is a test.\n\n",
        encoding="utf-8",
    )

    # 3. Setup Config
    config = Config(
        show_dir=show_dir,
        cache_dir=cache_dir,
        asr_provider="parakeet",  # User requested Parakeet
        tmdb_api_key="DUMMY",
    )

    engine = MatchEngine(config)

    # Warmup (load model)
    print("Warming up model...")
    t0 = time.time()
    # Just force load
    engine.asr._ensure_loaded()
    print(f"Model load time: {time.time() - t0:.2f}s")

    # Run Match
    print("Running match...")
    t_start = time.time()
    results = engine.process_path(season_dir)
    t_end = time.time()

    duration = t_end - t_start
    print(f"Total processing time: {duration:.2f}s")

    if duration < 5.0:
        print("SUCCESS: Performance goal met (<5s)")
    else:
        print(f"WARNING: Performance goal missed (Target <5s, Actual {duration:.2f}s)")


if __name__ == "__main__":
    benchmark()
