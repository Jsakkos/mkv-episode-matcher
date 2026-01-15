from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from mkv_episode_matcher.backend.dependencies import get_engine
from mkv_episode_matcher.core.engine import MatchEngineV2
from mkv_episode_matcher.core.models import MatchResult
from mkv_episode_matcher.backend.socket_manager import get_manager
import asyncio

router = APIRouter(prefix="/match", tags=["match"])

class MatchRequest(BaseModel):
    files: List[str]
    series_name: Optional[str] = None
    season: Optional[int] = None

class MatchResponse(BaseModel):
    status: str
    job_id: str

# Simple in-memory job store for demo purposes
# In production, use Redis or database
jobs = {}

@router.post("/start")
async def start_match(
    request: MatchRequest, 
    background_tasks: BackgroundTasks,
    engine: MatchEngineV2 = Depends(get_engine)
):
    job_id = f"job_{len(jobs) + 1}"
    jobs[job_id] = {"status": "pending", "results": [], "logs": []}
    
    background_tasks.add_task(process_matching_job, job_id, request, engine)
    
    return {"status": "started", "job_id": job_id}

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

async def process_matching_job(job_id: str, request: MatchRequest, engine: MatchEngineV2):
    manager = get_manager()
    loop = asyncio.get_event_loop()
    
    def progress_callback(current, total, filename):
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "progress",
                "job_id": job_id,
                "current": current,
                "total": total,
                "filename": str(filename)
            }),
            loop
        )

    def phase_callback(phase, message):
        asyncio.run_coroutine_threadsafe(
            manager.broadcast({
                "type": "phase_update",
                "job_id": job_id,
                "phase": phase,
                "message": message
            }),
            loop
        )

    try:
        jobs[job_id]["status"] = "processing"
        await manager.broadcast({"type": "job_update", "job_id": job_id, "status": "processing"})
        
        # Determine strict or auto season
        season_override = request.season
        
        paths = [Path(f) for f in request.files]
        parent_dir = paths[0].parent if paths else Path(".")
        
        # Run blocking engine call in thread pool
        matches, failures = await asyncio.to_thread(
            engine.process_path,
            path=parent_dir,
            season_override=season_override,
            files_override=paths,
            json_output=True,
            progress_callback=progress_callback,
            phase_callback=phase_callback
        )
        
        # Serialize results
        serialized_matches = []
        for m in matches:
             serialized_matches.append({
                 "original_file": str(m.matched_file),
                 "series": m.episode_info.series_name,
                 "season": m.episode_info.season,
                 "episode": m.episode_info.episode,
                 "title": m.episode_info.title,
                 "confidence": m.confidence
             })
             
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = serialized_matches
        jobs[job_id]["failures"] = [str(f.original_file) for f in failures]
        
        await manager.broadcast({
            "type": "job_complete",
            "job_id": job_id,
            "status": "completed",
            "results": serialized_matches,
            "failures": jobs[job_id]["failures"]
        })
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        await manager.broadcast({
            "type": "job_failed",
            "job_id": job_id,
            "error": str(e)
        })
