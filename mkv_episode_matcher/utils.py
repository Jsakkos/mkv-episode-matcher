# utils.py
import os
from PIL import Image
import imagehash
from typing import Optional, Set
from loguru import logger
import imageio.v3 as iio
import re

from tmdb_client import fetch_and_hash_season_images
from __main__ import CONFIG_FILE,CACHE_DIR
from concurrent.futures import ThreadPoolExecutor
import json
def check_filename(filename, series_title, season_number, episode_number):
    pattern = re.compile(f'{re.escape(series_title)} - S{season_number:02d}E{episode_number:02d}.mkv')
    return bool(pattern.match(filename))
def rename_episode_files(season_number,matching_episodes):
    for original_file_path in matching_episodes:
        series_title = os.path.basename(os.path.dirname(os.path.dirname(original_file_path)))
        original_file_name = os.path.basename(original_file_path)
        episode_number = matching_episodes[original_file_path]
        extension = os.path.splitext(original_file_path)[-1]
        new_file_name = f'{series_title} - S{season_number:02d}E{episode_number:02d}{extension}'
        new_file_path = os.path.join(os.path.dirname(original_file_path),new_file_name)
        if os.path.exists(new_file_path):
            logger.warning(f'Filename already exists: {new_file_name}.')
            new_file_name = f'{series_title} - S{season_number:02d}E{episode_number:02d}_2{extension}'
            new_file_path = os.path.join(os.path.dirname(original_file_path),new_file_name)
            logger.info(f'Renaming {original_file_name} -> {new_file_name}')
            os.rename(original_file_path,new_file_path)
        logger.info(f'Renaming {original_file_name} -> {new_file_name}')
        os.rename(original_file_path,new_file_path)
def rename_episode_file(original_file_path,season_number,episode_number):
        series_title = os.path.basename(os.path.dirname(os.path.dirname(original_file_path)))
        original_file_name = os.path.basename(original_file_path)
        extension = os.path.splitext(original_file_path)[-1]
        new_file_name = f'{series_title} - S{season_number:02d}E{episode_number:02d}{extension}'
        new_file_path = os.path.join(os.path.dirname(original_file_path),new_file_name)
        if os.path.exists(new_file_path):
            logger.warning(f'Filename already exists: {new_file_name}.')
            new_file_name = f'{series_title} - S{season_number:02d}E{episode_number:02d}_2{extension}'
            new_file_path = os.path.join(os.path.dirname(original_file_path),new_file_name)
            logger.info(f'Renaming {original_file_name} -> {new_file_name}')
            os.rename(original_file_path,new_file_path)
        logger.info(f'Renaming {original_file_name} -> {new_file_name}')
        os.rename(original_file_path,new_file_path)
def find_matching_episode(filepath: str, main_dir: str, season_number: int, season_hashes) -> Optional[int]:
    """
    Find the matching episode for a given video file by comparing frames with pre-loaded season hashes.

    Args:
        filepath (str): The path to the video file.
        main_dir (str): The main directory where the downloaded episode images are stored.
        season_number (int): The season number of the video file.
        season_hashes (Set[imagehash.ImageHash]): A set of perceptual hashes for all episode images in the season.

    Returns:
        Optional[int]: The episode number if a match is found, or None if no match is found.
    """
    metadata = iio.immeta(filepath)
    total_frames = int(metadata['fps']*metadata['duration'])
    frame_count = 2000
    match_episode = []
    match_locations = set()
    matched = False
    filename = os.path.basename(filepath)
    while not matched and frame_count < total_frames:
        frame_count += 1
        if frame_count % 10 == 0:  # Process every 10th frame
            frame = iio.imread(filepath, index=frame_count,plugin="pyav")
            frame_hash = calculate_image_hash(frame, is_path=False)
            for episode,hashes in season_hashes.items():
                for hash in hashes:
                    similar = hashes_are_similar(frame_hash,hash,threshold=5)
                    if similar:
                        match_episode.append(int(episode))
                        match_locations.add(frame_count)
                        logger.info(f"Matched video file {filename} with episode {episode} at frame {frame_count}")
                        frame_count+=100
            for value in set(match_episode):
                if match_episode.count(value) >= 5:
                    logger.info(f"The episode {value} appears at least 5 times in the list.")
                    matched=True
                    return value

    logger.warning(f"No matching episode found for video file {filepath}")
    return None
# def load_season_hashes(main_dir: str, season_number: int) -> Set[imagehash.ImageHash]:
#     """
#     Load perceptual hashes for all episode images in a given season.

#     Args:
#         main_dir (str): The main directory where the downloaded episode images are stored.
#         season_number (int): The season number to load hashes for.

#     Returns:
#         Set[imagehash.ImageHash]: A set of perceptual hashes for all episode images in the season.
#     """
#     hash_to_episode_map = {}
#     season_hashes = set()
#     season_dir = os.path.join(main_dir, f"downloaded_images")
#     logger.info(f'Season directory is: {season_dir}')
#     if os.path.exists(season_dir):
#         for episode_dir in os.listdir(season_dir):
            
#             episode_path = os.path.join(season_dir, episode_dir)
#             episode_number = int(episode_dir.split('_')[-1])
#             logger.info(f'Processing episode: {episode_number}')
#             for image_file in os.listdir(episode_path):
#                 image_path = os.path.join(episode_path, image_file)
#                 hash = calculate_image_hash(image_path, is_path=True)
#                 season_hashes.add(hash)
#                 hash_to_episode_map[hash] = episode_number
#     return season_hashes,hash_to_episode_map
def hashes_are_similar(hash1, hash2, threshold=20):
    """
    Determine if two perceptual hashes are similar within a given threshold.
    
    Args:
    - hash1, hash2: The perceptual hashes to compare.
    - threshold: The maximum allowed difference between the hashes for them to be considered similar.
    
    Returns:
    - True if hashes are similar within the threshold; False otherwise.
    """
    return abs(hash1 - hash2) <= threshold
def calculate_image_hash(data_or_path: bytes | str, is_path: bool = True) -> imagehash.ImageHash:
    """
    Calculate perceptual hash for given image data or file path.

    Args:
        data_or_path (bytes | str): If is_path is True, it's treated as a file path to an image;
            otherwise, it's binary data of an image.
        is_path (bool, optional): Flag indicating whether data_or_path is a file path (True) or binary data (False).
            Defaults to True.

    Returns:
        imagehash.ImageHash: The perceptual hash of the image.
    """
    if is_path:
        image = Image.open(data_or_path)
    else:
        # image = Image.open(BytesIO(data_or_path))
        image = Image.fromarray(data_or_path)

    hash = imagehash.average_hash(image)
    return hash

def load_show_hashes(show_name):
    json_file_path = os.path.join(CACHE_DIR,f"{show_name}_hashes.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            return json.load(json_file)
    else:
        return {}

def store_show_hashes(show_name, show_hashes):
    json_file_path = os.path.join(CACHE_DIR,f"{show_name}_hashes.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(show_hashes, json_file, default=lambda x: x.result() if isinstance(x, ThreadPoolExecutor) else x)
    logger.info(f"Show hashes saved to {json_file_path}")
def preprocess_hashes(show_name, show_id, seasons_to_process):
    """
    Preprocess hashes by loading them from the file or fetching and hashing them if necessary.

    Args:
        show_name (str): The name of the show.
        show_id (str): The TMDb ID of the show.
        seasons_to_process (list): A list of season numbers to process.

    Returns:
        dict: A dictionary containing the hashes for each season.
    """
    for season_number in seasons_to_process:
        existing_hashes = load_show_hashes(show_name)

        if str(season_number) in existing_hashes:
            logger.info(f"Skipping fetching and hashing images for Season {season_number}. Hashes already exist.")
            continue
        season_hashes = fetch_and_hash_season_images(show_id, season_number)
        existing_hashes[season_number] = season_hashes
        store_show_hashes(show_name, existing_hashes)
    # Convert hash values from strings back to appropriate type (e.g., integers)
    for season, episodes in existing_hashes.items():
        for episode_number, episode_hashes in episodes.items():
            existing_hashes[season][episode_number] = [imagehash.hex_to_hash(hash_str) for hash_str in episode_hashes]
    return existing_hashes

    
    