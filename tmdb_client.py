# tmdb_client.py
import requests
from loguru import logger
import os 
from concurrent.futures import ThreadPoolExecutor

def fetch_show_id(show_name, api_key):
    """
    Fetch the TMDb ID for a given show name.

    Args:
        show_name (str): The name of the show.
        api_key (str): The TMDb API key.

    Returns:
        str: The TMDb ID of the show, or None if not found.
    """
    url = f"https://api.themoviedb.org/3/search/tv?query={show_name}&api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return str(results[0]["id"])
    return None

def fetch_season_details(show_id: str, season_number: int, api_key: str) -> int:
    """
    Fetch the total number of episodes for a given show and season from the TMDb API.

    Args:
        show_id (str): The ID of the show on TMDb.
        season_number (int): The season number to fetch details for.
        api_key (str): The TMDb API key.

    Returns:
        int: The total number of episodes in the season, or 0 if the API request failed.
    """
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
    
def download_episode_images(show_id: str, season_number: int, episode_number: int, base_image_url: str, api_key: str, main_dir: str) -> None:
    """
    Download images for a specific episode from the TMDb API.

    Args:
        show_id (str): The ID of the show on TMDb.
        season_number (int): The season number of the episode.
        episode_number (int): The episode number to download images for.
        base_image_url (str): The base URL for image paths from the TMDb API.
        api_key (str): The TMDb API key.
        main_dir (str): The main directory where the downloaded images will be saved.
    """
    episode_image_dir = os.path.join(main_dir, f"downloaded_images/Season_{season_number}_Episode_{episode_number}")

    # Check if images already downloaded
    if os.path.exists(episode_image_dir) and len(os.listdir(episode_image_dir)) > 0:
        logger.info(f"Images for Season {season_number} Episode {episode_number} already downloaded.")
        return

    os.makedirs(episode_image_dir, exist_ok=True)

    # Construct the API URL for episode images
    url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}/episode/{episode_number}/images?api_key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        images = response.json().get('stills', [])
        for i, image in enumerate(images, start=1):
            image_url = base_image_url + image['file_path']
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                image_path = os.path.join(episode_image_dir, f"image_{i}.jpg")
                with open(image_path, 'wb') as file:
                    file.write(response.content)
                logger.info(f"Downloaded {image_url} to {image_path}")
            else:
                logger.error(f"Failed to download {image_url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch images for Season {season_number} Episode {episode_number}: {e}")

def download_season_images(show_id: str, season_number: int, base_image_url: str, api_key: str, main_dir: str) -> None:
    """
    Download images for all episodes of a given season.

    Args:
        show_id (str): The ID of the show on TMDb.
        season_number (int): The season number to download images for.
        base_image_url (str): The base URL for image paths from the TMDb API.
        api_key (str): The TMDb API key.
        main_dir (str): The main directory where the downloaded images will be saved.
    """
    season_dir = os.path.join(main_dir, f"downloaded_images/Season_{season_number}")

    # Check if season images already downloaded
    if os.path.exists(season_dir) and len(os.listdir(season_dir)) > 0:
        logger.info(f"Images for Season {season_number} already downloaded.")
        return

    total_episodes = fetch_season_details(show_id, season_number, api_key)

    with ThreadPoolExecutor() as executor:
        for episode_number in range(1, total_episodes + 1):
            executor.submit(download_episode_images, show_id, season_number, episode_number, base_image_url, api_key, main_dir)