# utils.py
import os
from PIL import Image
import imagehash
from typing import Optional, Set
from loguru import logger
import imageio.v3 as iio
import re

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
def find_matching_episode(filepath: str, main_dir: str, season_number: int, season_hashes: Set[imagehash.ImageHash],hash_to_episode_map) -> Optional[int]:
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
            for hash2 in season_hashes:
                similar = hashes_are_similar(frame_hash,hash2,threshold=5)
                if similar:
                    episode = hash_to_episode_map[hash2]
                    match_episode.append(episode)
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
def load_season_hashes(main_dir: str, season_number: int) -> Set[imagehash.ImageHash]:
    """
    Load perceptual hashes for all episode images in a given season.

    Args:
        main_dir (str): The main directory where the downloaded episode images are stored.
        season_number (int): The season number to load hashes for.

    Returns:
        Set[imagehash.ImageHash]: A set of perceptual hashes for all episode images in the season.
    """
    hash_to_episode_map = {}
    season_hashes = set()
    season_dir = os.path.join(main_dir, f"downloaded_images")
    logger.info(f'Season directory is: {season_dir}')
    if os.path.exists(season_dir):
        for episode_dir in os.listdir(season_dir):
            
            episode_path = os.path.join(season_dir, episode_dir)
            episode_number = int(episode_dir.split('_')[-1])
            logger.info(f'Processing episode: {episode_number}')
            for image_file in os.listdir(episode_path):
                image_path = os.path.join(episode_path, image_file)
                hash = calculate_image_hash(image_path, is_path=True)
                season_hashes.add(hash)
                hash_to_episode_map[hash] = episode_number
    return season_hashes,hash_to_episode_map
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