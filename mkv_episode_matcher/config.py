# config.py
import os
import configparser
import multiprocessing
from loguru import logger
def get_total_threads():
    return multiprocessing.cpu_count()
total_threads = get_total_threads()
MAX_THREADS = 4
logger.info(f"Total available threads: {total_threads} -> Setting max to {MAX_THREADS}")

def set_config(api_key, show_dir, file):
    config = configparser.ConfigParser()
    config["Config"] = {"api_key": str(api_key), "show_dir": show_dir,'max_threads':int(MAX_THREADS)}
    with open(file, "w") as configfile:
        config.write(configfile)

def get_config(file):
    config = configparser.ConfigParser()
    if os.path.exists(file):
        config.read(file)
        return config["Config"] if "Config" in config else None
    return {}
