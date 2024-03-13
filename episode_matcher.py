# episode_matcher.py
import os
from concurrent.futures import ThreadPoolExecutor
from .tmdb_client import fetch_show_id,download_season_images
from .utils import load_season_hashes, find_matching_episode, rename_episode_files

def process_show(api_key, show_dir):
    """
    Process the show by downloading episode images and finding matching episodes.

    Args:
        api_key (str): The TMDb API key.
        show_dir (str): The main directory of the show.
    """
    show_id = fetch_show_id(os.path.basename(show_dir), api_key)
    if show_id is None:
        print(f"Could not find show '{os.path.basename(show_dir)}' on TMDb.")
        return

    season_paths = [os.path.join(show_dir, d) for d in os.listdir(show_dir) if os.path.isdir(os.path.join(show_dir, d))]

    with ThreadPoolExecutor() as executor:
        for season_path in season_paths:
            season_number = int(os.path.basename(season_path).split()[-1])
            executor.submit(process_season, show_id, season_number, season_path)

def process_season(show_id, season_number, season_path):
    """
    Process a single season by downloading episode images and finding matching episodes.

    Args:
        show_id (str): The TMDb ID of the show.
        season_number (int): The season number.
        season_path (str): The path to the season directory.
    """
    download_season_images(show_id, season_number, season_path)
    season_hashes, hash_to_episode_map = load_season_hashes(season_path, season_number)
    matching_episodes = {}

    mkv_files = [os.path.join(season_path, f) for f in os.listdir(season_path) if f.endswith(".mkv")]
    for file in mkv_files:
        filepath = os.path.join(season_path, file)
        episode = find_matching_episode(filepath, season_path, season_number, season_hashes, hash_to_episode_map)
        matching_episodes[file] = episode

    rename_episode_files(season_number, matching_episodes)