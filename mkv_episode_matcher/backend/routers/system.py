from fastapi import APIRouter, Depends
from mkv_episode_matcher.backend.dependencies import get_engine
from mkv_episode_matcher import __version__

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def get_system_status():
    """
    Get current system status.
    Checks the singleton engine status without blocking.
    """
    from mkv_episode_matcher.backend.dependencies import get_engine_status
    
    status = get_engine_status()
    
    return {
        "status": status["status"],
        "model_loaded": status["loaded"],
        "version": __version__
    }

@router.get("/config")
def get_config():
    """Get current configuration."""
    from mkv_episode_matcher.core.config_manager import get_config_manager
    manager = get_config_manager()
    return manager.load().model_dump()

@router.post("/config")
def update_config(config_data: dict):
    """Update configuration."""
    from mkv_episode_matcher.core.config_manager import get_config_manager
    from mkv_episode_matcher.core.models import Config
    
    manager = get_config_manager()
    # Validate and update
    try:
        new_config = Config(**config_data)
        manager.save(new_config)
        return {"status": "success", "config": new_config.model_dump()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/config/validate")
def validate_config():
    """Check if required credentials are configured."""
    from mkv_episode_matcher.core.config_manager import get_config_manager
    
    manager = get_config_manager()
    config = manager.load()
    
    missing = []
    
    # Check OpenSubtitles credentials (required unless using local provider)
    if config.sub_provider == "opensubtitles":
        if not config.open_subtitles_api_key:
            missing.append("open_subtitles_api_key")
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "needs_onboarding": len(missing) > 0
    }

@router.post("/shutdown")
def shutdown_server():
    """Shutdown the application server."""
    import os
    import signal
    import threading
    import time
    
    def kill_server():
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
        
    # Schedule shutdown in a separate thread to allow response to return
    threading.Thread(target=kill_server).start()
    return {"status": "shutting_down"}
