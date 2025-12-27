from pathlib import Path

from rich import print

cache_dir = Path.home() / ".mkv-episode-matcher" / "cache" / "data"
print(f"Checking cache dir: {cache_dir}")

if not cache_dir.exists():
    print("[red]Cache dir does not exist[/red]")
else:
    for child in cache_dir.iterdir():
        if child.is_dir():
            print(f"[bold]{child.name}[/bold]")
            for f in child.glob("*.srt"):
                print(f"  - {f.name}")
