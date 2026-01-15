import threading
from mkv_episode_matcher.core.engine import MatchEngineV2
from mkv_episode_matcher.core.models import ConfigManager

# Global singleton instance
_engine_instance: MatchEngineV2 | None = None
_engine_lock = threading.Lock()
_parsing_status = "idle"  # idle, loading, ready, error

def get_config_manager():
    # Helper to get config, no caching needed here as ConfigManager handles it or is lightweight
    return ConfigManager()

def get_engine() -> MatchEngineV2:
    """
    Get the singleton instance of the MatchEngine.
    Initializes it if it hasn't been created yet.
    This call blocks until initialization is complete.
    """
    global _engine_instance, _parsing_status
    
    with _engine_lock:
        if _engine_instance is None:
            try:
                _parsing_status = "loading"
                manager = get_config_manager()
                _engine_instance = MatchEngineV2(manager.config)
                _parsing_status = "ready"
            except Exception as e:
                _parsing_status = "error"
                raise e
    
    return _engine_instance

def get_engine_status() -> dict:
    """Non-blocking status check."""
    return {
        "status": _parsing_status,
        "loaded": _engine_instance is not None
    }
