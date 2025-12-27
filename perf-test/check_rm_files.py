from pathlib import Path

from rich import print

cache_dir = Path.home() / ".mkv-episode-matcher" / "cache" / "data" / "Rick and Morty"
print(f"Checking cache dir: {cache_dir}")

if not cache_dir.exists():
    print("[red]Cache dir does not exist[/red]")
else:
    srt_files = list(cache_dir.glob("*.srt"))
    print(f"Found {len(srt_files)} SRT files. First 20:")
    for f in sorted(srt_files)[:20]:
        print(f"  - {f.name}")
