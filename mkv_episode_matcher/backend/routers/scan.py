from fastapi import APIRouter, Depends, HTTPException
from mkv_episode_matcher.backend.dependencies import get_engine
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
import os

router = APIRouter(prefix="/scan", tags=["scan"])

class FileEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None

@router.get("/browse", response_model=List[FileEntry])
async def browse_directory(path: Optional[str] = None):
    """
    List contents of a directory.
    If path is not provided, returns root drives (Windows) or logical roots.
    """
    if not path:
        drives = []
        import sys

        if sys.platform == "win32":
            import string
            from ctypes import windll

            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive_path = f"{letter}:\\"
                    drives.append(FileEntry(name=drive_path, path=drive_path, is_dir=True))
                bitmask >>= 1
        else:
            common_paths = [
                ("/", "Root (/)"),
                ("/home", "Home"),
                ("/mnt", "Mount points"),
                ("/media", "Removable media"),
                ("/opt", "Optional software"),
                ("/usr", "User programs"),
                ("/var", "Variable data"),
            ]
            for path_str, display_name in common_paths:
                path_obj = Path(path_str)
                if path_obj.exists() and path_obj.is_dir():
                    try:
                        next(path_obj.iterdir(), None)
                        drives.append(FileEntry(name=display_name, path=path_str, is_dir=True))
                    except (PermissionError, OSError):
                        continue

        return drives

    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    entries = []
    try:
        for item in p.iterdir():
            try:
                # Basic filtering so we don't crash on permission errors for individual files
                is_dir = item.is_dir()
                size = item.stat().st_size if not is_dir else None
                entries.append(FileEntry(
                    name=item.name,
                    path=str(item),
                    is_dir=is_dir,
                    size=size
                ))
            except PermissionError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Sort: directories first, then files
    entries.sort(key=lambda x: (not x.is_dir, x.name.lower()))
    return entries


@router.get("/test-subtitles")
async def test_subtitle_connection():
    """Test OpenSubtitles API connection and credentials."""
    from mkv_episode_matcher.core.config_manager import get_config_manager

    cm = get_config_manager()
    config = cm.load()

    result = {
        "api_key_configured": bool(config.open_subtitles_api_key),
        "username_configured": bool(config.open_subtitles_username),
        "password_configured": bool(config.open_subtitles_password),
        "connection_ok": False,
        "login_ok": False,
        "error": None,
    }

    if not config.open_subtitles_api_key:
        result["error"] = "OpenSubtitles API key not configured"
        return result

    try:
        from opensubtitlescom import OpenSubtitles

        client = OpenSubtitles(
            config.open_subtitles_user_agent,
            config.open_subtitles_api_key,
        )
        result["connection_ok"] = True

        if config.open_subtitles_username and config.open_subtitles_password:
            client.login(config.open_subtitles_username, config.open_subtitles_password)
            result["login_ok"] = True
    except Exception as e:
        result["error"] = str(e)

    return result


class AnalyzeRequest(BaseModel):
    path: str

@router.post("/analyze")
def analyze_path(req: AnalyzeRequest, engine=Depends(get_engine)):
    """
    Scan a directory for MKV files and perform initial context detection (Series/Season)
    without running the full ASR matching process.
    """
    path_obj = Path(req.path)
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    # Use engine's scan logic
    files = engine.scan_for_mkv(path_obj)
    
    results = []
    for f in files:
        # Detect context (Series, Season) using filename heuristics
        series, season = engine._detect_context(f)
        
        # Check if already processed (Scene Release format)
        is_processed = engine._is_already_processed(f)
        
        results.append({
            "path": str(f),
            "name": f.name,
            "series": series,
            "season": season,
            "is_processed": is_processed
        })
        
    return {
        "base_path": str(path_obj),
        "files": results,
        "count": len(results)
    }
