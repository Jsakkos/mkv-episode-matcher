# __main__.py
from .config import set_config
from .episode_matcher import process_show

def main():
    api_key = input("Enter your TMDb API key: ")
    show_dir = input("Enter the main directory of the show: ")

    set_config(api_key, show_dir)
    process_show(api_key, show_dir)

if __name__ == "__main__":
    main()