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
        # Return logical drives on Windows
        drives = []
        import string
        from ctypes import windll
        
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drives.append(FileEntry(name=drive_path, path=drive_path, is_dir=True))
            bitmask >>= 1
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
