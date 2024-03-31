# episode_matcher.py
import os
from concurrent.futures import ThreadPoolExecutor
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.tmdb_client import fetch_show_id
from mkv_episode_matcher.utils import load_show_hashes, find_matching_episode, rename_episode_file, check_filename,preprocess_hashes,scramble_filename,calculate_hashes,get_list_of_frames
from loguru import logger
import json
from mkv_episode_matcher.__main__ import CONFIG_FILE, CACHE_DIR
import pandas as pd
import numpy.random as npr
import numpy as np
# hash_data = {}
@logger.catch
def process_show(season=None, force=False, dry_run=False, threshold=None,hash_type=None):
    """
    Process the show by downloading episode images and finding matching episodes.

    Args:
        season (int, optional): The season number to process. If provided, only that season will be processed. Defaults to None.
        force (bool, optional): Whether to force re-processing of episodes even if they already exist. Defaults to False.
        dry_run (bool, optional): Whether to perform a dry run without actually processing the episodes. Defaults to False.
        threshold (float, optional): The threshold value for matching episodes. Defaults to None.
    """
    config = get_config(CONFIG_FILE)
    api_key = config.get("api_key")
    show_dir = config.get("show_dir")
    show_name = os.path.basename(show_dir)
    logger.info(f"Processing show '{show_name}'...")
    show_id = fetch_show_id(show_name)
    if show_id is None:
        logger.error(f"Could not find show '{os.path.basename(show_dir)}' on TMDb.")
        return

    season_paths = [os.path.join(show_dir, d) for d in os.listdir(show_dir) if os.path.isdir(os.path.join(show_dir, d))]
    logger.info(f"Found {len(season_paths)} seasons for show '{os.path.basename(show_dir)}'")
    seasons_to_process = [int(os.path.basename(season_path).split()[-1]) for season_path in season_paths]
    show_hashes = preprocess_hashes(show_name, show_id, seasons_to_process,hash_type=hash_type)

    # with ThreadPoolExecutor() as executor:
    if isinstance(season, int):
        # If a season number is provided then just process that one season
        for season_path in season_paths:
            season_number = int(os.path.basename(season_path).split()[-1])
            if season_number == season:
                try:
                    # Attempt to get hash from show_hashes and process the season
                    # executor.submit(process_season, show_id, season_number, season_path, show_hashes[str(season_number)], force, dry_run, threshold,hash_type)
                    process_season(show_id, season_number, season_path, show_hashes[str(season_number)], force, dry_run, threshold,hash_type)
                except KeyError:
                    # If a KeyError is raised then skip this season
                    logger.warning(f"Season {season} not found in show_hashes")
            else:
                # executor.submit(process_season, show_id, season_number, season_path, show_hashes[str(season_number)], force, dry_run, threshold,hash_type)
                process_season(show_id, season_number, season_path, show_hashes[str(season_number)], force, dry_run, threshold,hash_type)
    else:
        # Otherwise process all seasons available
        for season_path in season_paths:
            season_number = int(os.path.basename(season_path).split()[-1])
            try:
                # Attempt to get hash from show_hashes and process the season
                # executor.submit(process_season, show_id, season_number, season_path, show_hashes[str(season_number)], force, dry_run, threshold,hash_type)
                process_season(show_id, season_number, season_path, show_hashes[str(season_number)], force, dry_run, threshold,hash_type)
            except KeyError:
                # If a KeyError is raised then skip this season
                logger.warning(f"Season {season} not found in show_hashes")

    logger.info(f"Show '{os.path.basename(show_dir)}' processing completed")

@logger.catch
def process_season(show_id, season_number, season_path, season_hashes, force=False, dry_run=False, threshold=None,hash_type=None):
    """
    Process a single season by downloading episode images and finding matching episodes.

    Args:
        show_id (str): The TMDb ID of the show.
        season_number (int): The season number.
        season_path (str): The path to the season directory.
        season_hashes (dict): A dictionary containing the hashes of the episodes in the season.
        force (bool, optional): If True, forces the processing of the season even if it has already been processed. Defaults to False.
        dry_run (bool, optional): If True, performs a dry run without actually renaming the episode files. Defaults to False.
        threshold (float, optional): The matching threshold for finding matching episodes. Defaults to None.

    Returns:
        None
    """
    logger.info(f"Processing Season {season_number}...")
    config = get_config(CONFIG_FILE)
    show_dir = config.get("show_dir")
    show_name = os.path.basename(show_dir)
    n_episodes = len(season_hashes.keys())
    matching_episodes = {}

    mkv_files = [os.path.join(season_path, f) for f in os.listdir(season_path) if f.endswith(".mkv")]
    _ = [scramble_filename(original_file_path, i) for i, original_file_path in enumerate(mkv_files)]
    mkv_files = [os.path.join(season_path, f) for f in os.listdir(season_path) if f.endswith(".mkv")]
    frames_dict = {mkv_file: get_list_of_frames(mkv_file) for mkv_file in mkv_files}
    df = pd.DataFrame()
    # Initialize the dictionaries

    # Add existing_average_hashes data structure here
    for i in range(30):
        logger.info(f"Processing iteration {i+1}")
        frames_to_process = {mkv_file: npr.choice(frames_dict[mkv_file], 100, replace=False) for mkv_file in mkv_files}
        # Initialize results before the try block
        results = {}
        with ThreadPoolExecutor() as executor:
            if frames_to_process:
                try:
                    results = dict(executor.map(process_files, [(j, frames, mkv_file, season_hashes) for j, (mkv_file, frames) in enumerate(frames_to_process.items())]))
                except RuntimeError:
                    print("An error occurred while processing the video frames.")
            else:
                print("No more frames to process.")
        if len(results) == 0:
            continue
        for mkv_file, frames in frames_to_process.items():
            for frame in frames:
                if frame in frames_dict[mkv_file]:
                    frames_dict[mkv_file].remove(frame)
        x_values = []
        y_values = []
        labels = []
        for mkv_file, data in results.items():
            y = data['average'].min()
            x = data['average'].idxmin()
            x_values.append(x)
            y_values.append(y)
            labels.append(mkv_file)
        if df.empty:
            data = list(zip(x_values, y_values, labels))
            x_values, y_values, labels = zip(*data)
            df = pd.DataFrame([x_values, y_values, labels]).T
            df.columns =    ['episode_number', 'lowest_hash_comparison', 'filename']
            # convert the episode number to an integer
            df['episode_number'] = df['episode_number'].astype(int)
            # Sort the DataFrame by episode number

        else:
            for x, y, label in zip(x_values, y_values, labels):
                if label in df['filename'].values:
                    df.loc[df['filename'] == label, 'lowest_hash_comparison'] = y
                    df.loc[df['filename'] == label, 'episode_number'] = int(x)
                else:
                    new_row = {'episode_number': x, 'lowest_hash_comparison': y, 'filename': label}
                    df = df.append(new_row, ignore_index=True)
        df = df.sort_values(by='episode_number', ascending=True)
        logger.info(df)
        mkv_files = df.loc[df.episode_number.duplicated(keep=False),'filename'].to_list()
        logger.info(f"Matching duplicates: {len(mkv_files)}")
        if len(mkv_files) == 0:
            break
    for mkv_file in df.filename.unique():
        episode = df.loc[df['filename'] == mkv_file, 'episode_number'].values[0]
        if dry_run:
            logger.info(f'Skipping renaming of {os.path.basename(mkv_file)} with episode {episode}')
        else:
            rename_episode_file(mkv_file, season_number, episode)
 
def process_file(mkv_file, frames, existing_average_hashes):
    """
    Process the given MKV file by calculating the average hashes for each frame and comparing them
    with the existing average hashes.

    Args:
        mkv_file (str): The path of the MKV file to be processed.
        frames (list): A list of frames from the MKV file.
        existing_average_hashes (dict): A dictionary containing the existing average hashes for each episode.

    Returns:
        tuple: A tuple containing the MKV file path, a list of comparisons between the calculated hashes and
        the existing hashes, and a list of episode numbers corresponding to the comparisons.
    """
    processed_images = [calculate_hashes(mkv_file, image) for image in frames]
    average_hashes = {i: avg for i, avg in processed_images}
    a_comparisons = []
    a_episode_numbers = []

    for a_hash in average_hashes.values():
        for episode_number, episode_hashes in existing_average_hashes.items():
            for hash_val in episode_hashes:
                a_comparisons.append(abs(a_hash - hash_val))
                a_episode_numbers.append(episode_number)
    # Return the comparisons and episodes along with the filename
    return mkv_file, a_comparisons, a_episode_numbers

def process_files(args):
    i, frames, mkv_file, existing_average_hashes = args
    logger.info(f"Processing file {i+1}: {mkv_file}")
    mkv_file, a_comparisons, a_episode_numbers = process_file(mkv_file, frames, existing_average_hashes)
    # Define hash_data as an empty dictionary if it's not defined
    global hash_data
    if 'hash_data' not in globals():
        hash_data = {}
    # Check if the filename key exists in hash_data
    if mkv_file not in hash_data:
        # If not, create a new dictionary for that filename
        hash_data[mkv_file] = {
            'hash_comparisons': [],
            'episode_numbers': [],
            'frames_processed': []
        }
    
    # Extend the lists for hash_comparisons, episode_numbers, and frames_processed
    hash_data[mkv_file]['hash_comparisons'].extend(a_comparisons)
    hash_data[mkv_file]['episode_numbers'].extend(a_episode_numbers)
    hash_data[mkv_file]['frames_processed'].append(frames)
    # Calculate a_mean_lowest_5 using all the comparisons for that file
    df = pd.DataFrame({'episode_number': hash_data[mkv_file]['episode_numbers'], 'hash_comparison': hash_data[mkv_file]['hash_comparisons']})
    a_mean_lowest = df.groupby('episode_number')['hash_comparison'].apply(lambda x: np.mean(sorted(x)[:3]))
    return mkv_file, {'average': a_mean_lowest}