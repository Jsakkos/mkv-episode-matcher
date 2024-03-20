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
BASE_IMAGE_URL = "https://image.tmdb.org/t/p/original"

class RateLimitedRequest:
    def __init__(self, rate_limit=30, period=1):
        self.rate_limit = rate_limit  # Maximum number of requests allowed per period
        self.period = period  # Period in seconds
        self.requests_made = 0  # Counter for requests made
        self.start_time = time.time()  # Start time of the current period
        self.lock = Lock()  # Lock for synchronization

    def get(self, url):
        with self.lock:
            # Check if the rate limit has been reached
            if self.requests_made >= self.rate_limit:
                # Calculate the time to sleep until the start of the next period
                sleep_time = self.period - (time.time() - self.start_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                # Reset the counter and start time for the new period
                self.requests_made = 0
                self.start_time = time.time()

            # Increment the counter
            self.requests_made += 1

        # Make the request
        response = requests.get(url)
        return response

# Initialize rate-limited request
rate_limited_request = RateLimitedRequest(rate_limit=30, period=1)
def calculate_image_hash_from_url(image_url):
    try:
        response = rate_limited_request.get(image_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return str(imagehash.average_hash(img))
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
    
# def download_episode_images(show_id, season_number, episode_number, season_path):
#     """
#     Download images for a specific episode from the TMDb API.

#     Args:
#         show_id (str): The ID of the show on TMDb.
#         season_number (int): The season number of the episode.
#         episode_number (int): The episode number to download images for.
#     """
#     logger.info(f"Downloading images for Season {season_number} Episode {episode_number}...")
#     episode_image_dir = os.path.join(season_path, f"downloaded_images/Season_{season_number}_Episode_{episode_number}")
#     logger.info(f"Episode image directory: {episode_image_dir}")

#     # Check if images already downloaded
#     if os.path.exists(episode_image_dir) and len(os.listdir(episode_image_dir)) > 0:
#         logger.info(f"Images for Season {season_number} Episode {episode_number} already downloaded.")
#         return

#     os.makedirs(episode_image_dir, exist_ok=True)

#     # Construct the API URL for episode images
#     config = get_config(CONFIG_FILE)
#     api_key = config.get("api_key")
#     url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}/episode/{episode_number}/images?api_key={api_key}"
#     logger.debug(f"API URL: {url}")
#     try:
#         logger.info(f"Fetching images for Season {season_number} Episode {episode_number}...")
#         response = requests.get(url)
#         response.raise_for_status()
#         images = response.json().get('stills', [])
#         for i, image in enumerate(images, start=1):
#             image_url = BASE_IMAGE_URL + image['file_path']
#             response = requests.get(image_url, stream=True)
#             if response.status_code == 200:
#                 image_path = os.path.join(episode_image_dir, f"image_{i}.jpg")
#                 with open(image_path, 'wb') as file:
#                     file.write(response.content)
#                 logger.info(f"Downloaded {image_url} to {image_path}")
#             else:
#                 logger.error(f"Failed to download {image_url}")
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Failed to fetch images for Season {season_number} Episode {episode_number}: {e}")

# def download_season_images(show_id, season_number, season_path):
#     """
#     Download images for all episodes of a given season.

#     Args:
#         show_id (str): The ID of the show on TMDb.
#         season_number (int): The season number to download images for.
#         season_path (str): The path where the downloaded images will be saved.
#     """
#     logger.info(f"Downloading images for Season {season_number}...")
#     season_dir = os.path.join(season_path, f"downloaded_images/Season_{season_number}")

#     # Check if season images already downloaded
#     if os.path.exists(season_dir) and len(os.listdir(season_dir)) > 0:
#         logger.info(f"Images for Season {season_number} already downloaded.")
#         return

#     total_episodes = fetch_season_details(show_id, season_number)

#     with ThreadPoolExecutor() as executor:
#         for episode_number in range(1, total_episodes + 1):
#             executor.submit(download_episode_images, show_id, season_number, episode_number, season_path)
#     return total_episodes
def fetch_and_hash_episode_images(show_id, season_number, episode_number):
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
            hash_value = calculate_image_hash_from_url(image_url)
            hashes.append(hash_value)

        return hashes

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch images for Season {season_number} Episode {episode_number}: {e}")
        return None

def fetch_and_hash_season_images(show_id, season_number):
    logger.info(f"Fetching images for Season {season_number}...")

    total_episodes = fetch_season_details(show_id, season_number)
    episode_hashes = {}
    lock = Lock()  # Lock for synchronization
    config = get_config(CONFIG_FILE)
    MAX_THREADS = config.get('max_threads')
    with ThreadPoolExecutor(max_workers=int(MAX_THREADS)) as executor:
        futures = []
        for episode_number in range(1, total_episodes + 1):
            future = executor.submit(fetch_and_hash_episode_images, show_id, season_number, episode_number)
            futures.append((episode_number, future))

        # Collect results and update the episode hashes dictionary
        for episode_number, future in futures:
            hashes = future.result()
            with lock:
                episode_hashes[episode_number] = hashes

    return episode_hashes