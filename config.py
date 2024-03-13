# config.py

TMDB_API_KEY = None
SHOW_MAIN_DIR = None

def set_config(api_key, show_dir):
    global TMDB_API_KEY, SHOW_MAIN_DIR
    TMDB_API_KEY = api_key
    SHOW_MAIN_DIR = show_dir