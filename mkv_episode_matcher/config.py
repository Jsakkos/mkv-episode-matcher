# config.py
import os
import configparser
import multiprocessing
from loguru import logger

MAX_THREADS = 4

def get_total_threads():
    return multiprocessing.cpu_count()
total_threads = get_total_threads()

logger.info(f"Total available threads: {total_threads} -> Setting max to {MAX_THREADS}")



def set_config(tmdb_api_key, open_subtitles_api_key,open_subtitles_user_agent,open_subtitles_username,open_subtitles_password,show_dir, file,tesserect_path=None):
    config = configparser.ConfigParser()
    config["Config"] = {"tmdb_api_key": str(tmdb_api_key), "show_dir": show_dir,'max_threads':int(MAX_THREADS),'open_subtitles_api_key':str(open_subtitles_api_key),'open_subtitles_user_agent':str(open_subtitles_user_agent),'open_subtitles_username':str(open_subtitles_username),'open_subtitles_password':str(open_subtitles_password),'tesserect_path':str(tesserect_path)}
    logger.info(f'Setting config with API:{tmdb_api_key}, show_dir: {show_dir}, and max_threads: {MAX_THREADS}')
    with open(file, "w") as configfile:
        config.write(configfile)

def get_config(file):
    logger.info(f'Loading config from {file}')
    config = configparser.ConfigParser()
    if os.path.exists(file):
        config.read(file)
        return config["Config"] if "Config" in config else None
    return {}
