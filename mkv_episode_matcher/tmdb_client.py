# tmdb_client.py
import requests
from loguru import logger
import os 
from concurrent.futures import ThreadPoolExecutor
from mkv_episode_matcher.config import get_config
from mkv_episode_matcher.__main__ import CONFIG_FILE,CACHE_DIR
from threading import Lock
import time
from io import BytesIO
from PIL import Image
import imagehash
from imagehash import ImageHash
import numpy as np
import cv2
BASE_IMAGE_URL = "https://image.tmdb.org/t/p/original"
def average_hash(image, hash_size=8, mean=np.mean):
    if hash_size < 2:
        raise ValueError('Hash size must be greater than or equal to 2')

    # Convert the image to grayscale and resize it
    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    resized_image = cv2.resize(gray_image, (hash_size, hash_size))

    # Find the average pixel value
    avg = mean(resized_image)

    # Create string of bits
    diff = resized_image > avg

    # Make a hash
    return ImageHash(diff)
class RateLimitedRequest:
    """
    A class that represents a rate-limited request object.

    Attributes:
        rate_limit (int): Maximum number of requests allowed per period.
        period (int): Period in seconds.
        requests_made (int): Counter for requests made.
        start_time (float): Start time of the current period.
        lock (Lock): Lock for synchronization.
    """

    def __init__(self, rate_limit=30, period=1):
        self.rate_limit = rate_limit
        self.period = period
        self.requests_made = 0
        self.start_time = time.time()
        self.lock = Lock()

    def get(self, url):
        """
        Sends a rate-limited GET request to the specified URL.

        Args:
            url (str): The URL to send the request to.

        Returns:
            Response: The response object returned by the request.
        """
        with self.lock:
            if self.requests_made >= self.rate_limit:
                sleep_time = self.period - (time.time() - self.start_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.requests_made = 0
                self.start_time = time.time()

            self.requests_made += 1

        response = requests.get(url)
        return response

# Initialize rate-limited request
rate_limited_request = RateLimitedRequest(rate_limit=30, period=1)
def calculate_image_hash_from_url(image_url,hash_type):
    """
    Calculate the image hash from the given image URL.

    Parameters:
    image_url (str): The URL of the image.

    Returns:
    str: The calculated image hash as a string, or None if there was an error.

    """
    try:
        response = rate_limited_request.get(image_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            if hash_type == 'phash':
                return str(imagehash.phash(img))
            elif hash_type == 'average':
                return str(imagehash.average_hash(img))
            elif hash_type =='fast':
                return str(average_hash(img))
        else:
            logger.error(f"Failed to download {image_url}")
            return None
    except Exception as e:
        logger.error(f"Error processing image: {image_url}: {e}")
        return None
def fetch_show_id(show_name):
    """
    Fetch the TMDb ID for a given show name.

    Args:
        show_name (str): The name of the show.

    Returns:
        str: The TMDb ID of the show, or None if not found.
    """
    config = get_config(CONFIG_FILE)
    api_key = config.get("api_key")
    url = f"https://api.themoviedb.org/3/search/tv?query={show_name}&api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return str(results[0]["id"])
    return None

def fetch_season_details(show_id, season_number):
    """
    Fetch the total number of episodes for a given show and season from the TMDb API.

    Args:
        show_id (str): The ID of the show on TMDb.
        season_number (int): The season number to fetch details for.

    Returns:
        int: The total number of episodes in the season, or 0 if the API request failed.
    """
    logger.info(f"Fetching season details for Season {season_number}...")
    config = get_config(CONFIG_FILE)
    api_key = config.get("api_key")
    url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}?api_key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        season_data = response.json()
        total_episodes = len(season_data.get('episodes', []))
        return total_episodes
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch season details for Season {season_number}: {e}")
        return 0
    except KeyError:
        logger.error(f"Missing 'episodes' key in response JSON data for Season {season_number}")
        return 0
    
def fetch_and_hash_episode_images(show_id, season_number, episode_number,hash_type):
    """
    Fetches and hashes the images for a specific episode of a TV show.

    Args:
        show_id (int): The ID of the TV show.
        season_number (int): The season number of the episode.
        episode_number (int): The episode number.

    Returns:
        list: A list of hash values for the episode images.

    Raises:
        requests.exceptions.RequestException: If there is an error while fetching the images.

    """
    logger.info(f"Fetching and hashing images for Season {season_number} Episode {episode_number}...")

    # Construct the API URL for episode images
    config = get_config(CONFIG_FILE)
    api_key = config.get("api_key")
    url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}/episode/{episode_number}/images?api_key={api_key}"
    logger.debug(f"API URL: {url}")

    try:
        logger.info(f"Fetching images for Season {season_number} Episode {episode_number}...")
        response = rate_limited_request.get(url)
        response.raise_for_status()
        images = response.json().get('stills', [])

        hashes = []
        for i, image in enumerate(images, start=1):
            image_url = BASE_IMAGE_URL + image['file_path']
            hash_value = calculate_image_hash_from_url(image_url,hash_type)
            hashes.append(hash_value)

        return hashes

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch images for Season {season_number} Episode {episode_number}: {e}")
        return None

def fetch_and_hash_season_images(show_id: int, season_number: int,hash_type) -> None:
    """
    Fetches and hashes the images for a given season of a TV show.

    Args:
        show_id (int): The ID of the TV show.
        season_number (int): The season number.

    Returns:
        dict: A dictionary containing the episode numbers as keys and their corresponding image hashes as values.
    """
    logger.info(f"Fetching images for Season {season_number}...")

    total_episodes = fetch_season_details(show_id, season_number)
    episode_hashes = {}
    lock = Lock()  # Lock for synchronization
    config = get_config(CONFIG_FILE)
    MAX_THREADS = config.get('max_threads')
    with ThreadPoolExecutor(max_workers=int(MAX_THREADS)) as executor:
        futures = []
        for episode_number in range(1, total_episodes + 1):
            future = executor.submit(fetch_and_hash_episode_images, show_id, season_number, episode_number,hash_type)
            futures.append((episode_number, future))

        # Collect results and update the episode hashes dictionary
        for episode_number, future in futures:
            hashes = future.result()
            with lock:
                episode_hashes[episode_number] = hashes

    return episode_hashes