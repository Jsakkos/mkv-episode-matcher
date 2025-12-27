from pathlib import Path

from rich import print

cache_dir = Path.home() / ".mkv-episode-matcher" / "cache" / "data" / "The Expanse"
print(f"Checking cache dir: {cache_dir}")

if not cache_dir.exists():
    print("[red]Cache dir does not exist[/red]")
    # Check parent to see if it's named differently
    parent = cache_dir.parent
    if parent.exists():
        print("Available shows:")
        for child in parent.iterdir():
            if "expanse" in child.name.lower():
                print(f"  - {child.name}")
else:
    srt_files = list(cache_dir.glob("*.srt"))
    print(f"Found {len(srt_files)} SRT files.")
    for f in sorted(srt_files)[:5]:
        print(f"  - {f.name}")
