import re
from pathlib import Path
from typing import Optional


def generate_subtitle_patterns(
    series_name: str, season: int, episode: int
) -> list[str]:
    """
    Generate various common subtitle filename patterns.

    Args:
        series_name (str): Name of the series
        season (int): Season number
        episode (int): Episode number

    Returns:
        List[str]: List of possible subtitle filenames
    """
    patterns = [
        # Standard format: "Show Name - S01E02.srt"
        f"{series_name} - S{season:02d}E{episode:02d}.srt",
        # Season x Episode format: "Show Name - 1x02.srt"
        f"{series_name} - {season}x{episode:02d}.srt",
        # Separate season/episode: "Show Name - Season 1 Episode 02.srt"
        f"{series_name} - Season {season} Episode {episode:02d}.srt",
        # Compact format: "ShowName.S01E02.srt"
        f"{series_name.replace(' ', '')}.S{season:02d}E{episode:02d}.srt",
        # Numbered format: "Show Name 102.srt"
        f"{series_name} {season:01d}{episode:02d}.srt",
        # Dot format: "Show.Name.1x02.srt"
        f"{series_name.replace(' ', '.')}.{season}x{episode:02d}.srt",
        # Underscore format: "Show_Name_S01E02.srt"
        f"{series_name.replace(' ', '_')}_S{season:02d}E{episode:02d}.srt",
    ]

    return patterns


def find_existing_subtitle(
    series_cache_dir: str, series_name: str, season: int, episode: int
) -> Optional[str]:
    """
    Check for existing subtitle files in various naming formats.

    Args:
        series_cache_dir (str): Directory containing subtitle files
        series_name (str): Name of the series
        season (int): Season number
        episode (int): Episode number

    Returns:
        Optional[str]: Path to existing subtitle file if found, None otherwise
    """
    patterns = generate_subtitle_patterns(series_name, season, episode)

    for pattern in patterns:
        filepath = Path(series_cache_dir) / pattern
        if filepath.exists():
            return filepath

    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename
    """
    # Replace problematic characters
    filename = filename.replace(":", " -")
    filename = filename.replace("/", "-")
    filename = filename.replace("\\", "-")

    # Remove any other invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)

    return filename.strip()
