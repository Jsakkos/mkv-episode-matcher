import sys

from mkv_episode_matcher.cli import app as cli_app, serve


def main():
    """Entry point for the application.
    
    If no arguments are provided, defaults to launching the web server.
    This makes the executable user-friendly when double-clicked.
    """
    # If no arguments provided (e.g., double-clicking the exe), default to serve
    if len(sys.argv) == 1:
        # Call serve directly with defaults
        serve(port=8001, host="0.0.0.0", no_browser=False)
    else:
        cli_app()


if __name__ == "__main__":
    main()
