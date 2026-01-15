from fastapi import APIRouter, Depends
from mkv_episode_matcher.backend.dependencies import get_engine

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
        "version": "1.1"
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
