# config.py
import os
import configparser

def set_config(api_key, show_dir, file):
    config = configparser.ConfigParser()
    config["Config"] = {"api_key": api_key, "show_dir": show_dir}
    with open(file, "w") as configfile:
        config.write(configfile)

def get_config(file):
    config = configparser.ConfigParser()
    if os.path.exists(file):
        config.read(file)
        return dict(config.items("Config")) if "Config" in config else {}
    return {}
