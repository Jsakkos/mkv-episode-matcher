
import sys
import uvicorn
from mkv_episode_matcher.backend.main import app
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8001")

def main():
    """Entry point for the application."""
    # Start browser in background
    if "--no-browser" not in sys.argv:
        threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()
