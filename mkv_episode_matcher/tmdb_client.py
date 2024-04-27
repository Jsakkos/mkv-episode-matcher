# tmdb_client.py
import time
from threading import Lock

import requests
from loguru import logger

from mkv_episode_matcher.__main__ import CONFIG_FILE
from mkv_episode_matcher.config import get_config

BASE_IMAGE_URL = "https://image.tmdb.org/t/p/original"


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


def fetch_show_id(show_name):
    """
    Fetch the TMDb ID for a given show name.

    Args:
        show_name (str): The name of the show.

    Returns:
        str: The TMDb ID of the show, or None if not found.
    """
    config = get_config(CONFIG_FILE)
    tmdb_api_key = config.get("tmdb_api_key")
    url = f"https://api.themoviedb.org/3/search/tv?query={show_name}&api_key={tmdb_api_key}"
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
    tmdb_api_key = config.get("tmdb_api_key")
    url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}?api_key={tmdb_api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        season_data = response.json()
        total_episodes = len(season_data.get("episodes", []))
        return total_episodes
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch season details for Season {season_number}: {e}")
        return 0
    except KeyError:
        logger.error(
            f"Missing 'episodes' key in response JSON data for Season {season_number}"
        )
        return 0


def get_number_of_seasons(show_id):
    """
    Retrieves the number of seasons for a given TV show from the TMDB API.

    Parameters:
    - show_id (int): The ID of the TV show.

    Returns:
    - num_seasons (int): The number of seasons for the TV show.

    Raises:
    - requests.HTTPError: If there is an error while making the API request.
    """
    config = get_config(CONFIG_FILE)
    tmdb_api_key = config.get("tmdb_api_key")
    url = f"https://api.themoviedb.org/3/tv/{show_id}?api_key={tmdb_api_key}"
    response = requests.get(url)
    response.raise_for_status()
    show_data = response.json()
    num_seasons = show_data.get("number_of_seasons", 0)
    logger.info(f"Found {num_seasons} seasons")
    return num_seasons
