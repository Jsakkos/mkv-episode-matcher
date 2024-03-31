# utils.py
import os
from PIL import Image
import imagehash
from typing import Optional, Set
from loguru import logger
import imageio.v3 as iio
import re
from collections import defaultdict
from mkv_episode_matcher.tmdb_client import fetch_and_hash_season_images
from mkv_episode_matcher.__main__ import CONFIG_FILE,CACHE_DIR
from concurrent.futures import ThreadPoolExecutor
import statistics
import json
import warnings
import sys
import traceback
import numpy as np
def check_filename(filename, series_title, season_number, episode_number):
    """
    Check if a filename matches the expected naming convention for a series episode.

    Args:
        filename (str): The filename to be checked.
        series_title (str): The title of the series.
        season_number (int): The season number of the episode.
        episode_number (int): The episode number of the episode.

    Returns:
        bool: True if the filename matches the expected naming convention, False otherwise.

    This function checks if the given filename matches the expected naming convention for a series episode.
    The expected naming convention is '{series_title} - S{season_number:02d}E{episode_number:02d}.mkv'.
    If the filename matches the expected pattern, it returns True; otherwise, it returns False.

    Example:
        If filename = 'Example - S01E03.mkv', series_title = 'Example', season_number = 1, and episode_number = 3,
        the function will return True because the filename matches the expected pattern.
    """
    pattern = re.compile(f'{re.escape(series_title)} - S{season_number:02d}E{episode_number:02d}.mkv')
    return bool(pattern.match(filename))
def scramble_filename(original_file_path, file_number):
    """
    Scrambles the filename of the given file path by adding the series title and file number.

    Args:
        original_file_path (str): The original file path.
        file_number (int): The file number to be added to the filename.

    Returns:
        None
    """
    logger.info(f'Scrambling {original_file_path}')
    series_title = os.path.basename(os.path.dirname(os.path.dirname(original_file_path)))
    original_file_name = os.path.basename(original_file_path)
    extension = os.path.splitext(original_file_path)[-1]
    new_file_name = f'{series_title} - {file_number:03d}{extension}'
    new_file_path = os.path.join(os.path.dirname(original_file_path), new_file_name)
    if not os.path.exists(new_file_path):
        logger.info(f'Renaming {original_file_name} -> {new_file_name}')
        os.rename(original_file_path, new_file_path)
def rename_episode_file(original_file_path, season_number, episode_number):
    """
    Rename an episode file with a standardized naming convention.

    Args:
        original_file_path (str): The original file path of the episode.
        season_number (int): The season number of the episode.
        episode_number (int): The episode number of the episode.

    Returns:
        None

    This function renames an episode file with a standardized naming convention based on the series title, season number,
    and episode number. If a file with the intended new name already exists, it appends a numerical suffix to the filename
    until it finds a unique name.

    Example:
        If original_file_path = '/path/to/episode.mkv', season_number = 1, and episode_number = 3, and the series title is 'Example',
        the function will rename the file to 'Example - S01E03.mkv' if no file with that name already exists. If a file with that
        name already exists, it will be renamed to 'Example - S01E03_2.mkv', and so on.
    """
    series_title = os.path.basename(os.path.dirname(os.path.dirname(original_file_path)))
    original_file_name = os.path.basename(original_file_path)
    extension = os.path.splitext(original_file_path)[-1]
    new_file_name = f'{series_title} - S{season_number:02d}E{episode_number:02d}{extension}'
    new_file_path = os.path.join(os.path.dirname(original_file_path), new_file_name)

    # Check if the new file path already exists
    if os.path.exists(new_file_path):
        logger.warning(f'Filename already exists: {new_file_name}.')
        
        # If the file already exists, find a unique name by appending a numerical suffix
        suffix = 2
        while True:
            new_file_name = f'{series_title} - S{season_number:02d}E{episode_number:02d}_{suffix}{extension}'
            new_file_path = os.path.join(os.path.dirname(original_file_path), new_file_name)
            if not os.path.exists(new_file_path):
                break
            suffix += 1
        
        logger.info(f'Renaming {original_file_name} -> {new_file_name}')
        os.rename(original_file_path, new_file_path)
    else:
        logger.info(f'Renaming {original_file_name} -> {new_file_name}')
        os.rename(original_file_path, new_file_path)


def find_matching_episode(filepath: str, main_dir: str, season_number: int, season_hashes, hash_type,matching_threshold=None,) -> Optional[int]:
    """
    Find the matching episode for a given video file by comparing frames with pre-loaded season hashes.

    Args:
        filepath (str): The path to the video file.
        main_dir (str): The main directory where the downloaded episode images are stored.
        season_number (int): The season number of the video file.
        season_hashes (Set[imagehash.ImageHash]): A set of perceptual hashes for all episode images in the season.
        matching_threshold (Optional[int]): The threshold for determining similarity between image hashes. If not provided, a default threshold will be used.

    Returns:
        Optional[int]: The episode number if a match is found, or None if no match is found.
    """
    try:
        metadata = iio.immeta(filepath)
        total_frames = int(metadata['fps'] * metadata['duration'])
        frame_count = 0
        matching_episodes = defaultdict(set) 
        hamming_distances = defaultdict(list)
        matched = False
        max_retries = 3
        retries = 0
        filename = os.path.basename(filepath)
        if matching_threshold is not None:
            threshold = matching_threshold
        required_matches = min(5, len(season_hashes)) 
        while not matched and frame_count < total_frames:
            frame_count += 1
            if frame_count % 10 == 0:  # Process every 10th frame
                frame = iio.imread(filepath, index=frame_count, plugin="pyav")
                frame_hash = calculate_image_hash(frame, False,hash_type)
                for episode, hashes in season_hashes.items():
                    for i, hash_val in enumerate(hashes):
                        similar, hamming_distance = hashes_are_similar(frame_hash, hash_val, threshold=threshold)
                        if similar:
                            logger.info(f"Matched video file {filepath} at frame {frame_count} with episode {episode} - hash {i} - distance: {hamming_distance}")
                            matching_episodes[episode].add(i)
                            hamming_distances[episode].append(hamming_distance) 
                            if len(matching_episodes[episode]) >= required_matches:
                                # Calculate mean hamming distance for each episode and return the episode with the lowest mean distance
                                # mean_distances = {episode: sum(distances) / len(distances) for episode, distances in hamming_distances.items()}
                                median_distances = {episode: statistics.median(distances) for episode, distances in hamming_distances.items()}
                                best_episode = min(median_distances, key=median_distances.get)
                                logger.info(f"Best match for video file {filepath} is episode {best_episode} with median Hamming distance {median_distances[best_episode]}")
                                matched = True
                                return int(best_episode),median_distances
                            frame_count += 500
                if frame_count >= total_frames:
                    frame_count = 0
                    threshold += 1
                    retries += 1
                    logger.warning(f"No matching episode found for video file {filepath}. Restarting search with threshold of {threshold}")
                    if retries >= max_retries:
                        logger.warning(f'Unable to match {filepath}')
                        break
        return None

    except Exception as e:
        logger.error(f"Error processing file {filepath}: {e}")
        return None

def get_list_of_frames(mkv_file):
    """
    Get a list of all frames in an MKV file.

    Parameters:
    mkv_file (str): The path to the MKV file.

    Returns:
    list: A list of all frames in the MKV file.
    """
    metadata = iio.immeta(mkv_file)
    total_frames = int(metadata['fps'] * metadata['duration'])
    # Create a list of all frames
    all_frames = list(range(total_frames-1))
    return all_frames
def hashes_are_similar(hash1, hash2, threshold=20):
    """
    Determine if two perceptual hashes are similar within a given threshold.
    
    Args:
    - hash1: The first perceptual hash to compare.
    - hash2: The second perceptual hash to compare.
    - threshold: The maximum allowed difference between the hashes for them to be considered similar.
    
    Returns:
    - A tuple containing two values:
        - A boolean value indicating whether the hashes are similar within the threshold.
        - The hamming distance between the hashes.
    """
    hamming_distance = abs(hash1 - hash2)
    return hamming_distance <= threshold, hamming_distance
def calculate_image_hash(data_or_path: bytes | str, is_path: bool = True,hash_type='average') -> imagehash.ImageHash:
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
    if hash_type == 'average':
        hash = imagehash.average_hash(image)
    elif hash_type == 'phash':
        hash = imagehash.phash(image)
    return hash
@logger.catch
def calculate_hashes(mkv_file, frame_count):
    """
    Calculate the image hash for a given frame in an MKV file.

    Args:
        mkv_file (str): The path to the MKV file.
        frame_count (int): The index of the frame to calculate the hash for.

    Returns:
        tuple: A tuple containing the frame count and the calculated image hash.

    Raises:
        Exception: If an error occurs during the calculation.

    """
    try:
        frame = iio.imread(mkv_file, index=frame_count, plugin="pyav")
    except Exception as e:
        logger.error(f"Error reading frame {frame_count} from {mkv_file}: {e}")
        frame = np.zeros((8,8))
    average_hash = calculate_image_hash(frame, False, 'average')
    return frame_count, average_hash

def load_show_hashes(show_name,hash_type):
    """
    Load the hashes for a given show from a JSON file.

    Args:
        show_name (str): The name of the show.

    Returns:
        dict: A dictionary containing the loaded hashes, or an empty dictionary if the JSON file doesn't exist.
    """
    json_file_path = os.path.join(CACHE_DIR, f"{show_name}_hashes_{hash_type}.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            return json.load(json_file)
    else:
        return {}

def store_show_hashes(show_name, show_hashes,hash_type):
    """
    Stores the hashes of a show in a JSON file.

    Args:
        show_name (str): The name of the show.
        show_hashes (dict): A dictionary containing the hashes of the show.

    Returns:
        None
    """
    json_file_path = os.path.join(CACHE_DIR, f"{show_name}_hashes_{hash_type}.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(show_hashes, json_file, default=lambda x: x.result() if isinstance(x, ThreadPoolExecutor) else x)
    logger.info(f"Show hashes saved to {json_file_path}")
def preprocess_hashes(show_name, show_id, seasons_to_process,hash_type):
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
        existing_hashes = load_show_hashes(show_name,hash_type)

        if str(season_number) in existing_hashes:
            logger.info(f"Skipping fetching and hashing images for Season {season_number}. Hashes already exist.")
            continue
        season_hashes = fetch_and_hash_season_images(show_id, season_number,hash_type)
        existing_hashes[season_number] = season_hashes
        store_show_hashes(show_name, existing_hashes,hash_type)
    # Convert hash values from strings back to appropriate type (e.g., integers)
    for season, episodes in existing_hashes.items():
        for episode_number, episode_hashes in episodes.items():
            existing_hashes[season][episode_number] = [imagehash.hex_to_hash(hash_str) for hash_str in episode_hashes]
    return existing_hashes

    
    