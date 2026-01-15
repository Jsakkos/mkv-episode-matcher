from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
from mkv_episode_matcher.backend.routers import scan, match, system
import mimetypes
from pathlib import Path

app = FastAPI(
    title="MKV Episode Matcher",
    description="Backend API for MKV Episode Matcher",
    version="1.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from mkv_episode_matcher.backend.routers import websocket
app.include_router(websocket.router)

app.include_router(scan.router)
app.include_router(match.router)
app.include_router(system.router)

# Fix MIME types on Windows - Validated Middleware Approach
@app.middleware("http")
async def fix_mime_type_middleware(request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(".js"):
        response.headers["content-type"] = "application/javascript"
    elif request.url.path.endswith(".css"):
        response.headers["content-type"] = "text/css"
    return response

# Mount static files (Frontend)
# In development, use ../frontend/dist
# In production (bundled), use ./frontend
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if not static_dir.exists():
    # Fallback to local 'frontend' dir if bundled flat
    static_dir = Path(__file__).parent / "frontend"

if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Check if file exists
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            # Manually handle root files MIME types if needed
            if file_path.name.endswith('.js'):
                return FileResponse(file_path, media_type='application/javascript')
            return FileResponse(file_path)
            
        # SPA Fallback
        return FileResponse(static_dir / "index.html")

@app.on_event("startup")
async def startup_event():
    import threading
    from mkv_episode_matcher.backend.dependencies import get_engine
    
    logger.info("Starting MKV Episode Matcher API")
    
    def warm_up_engine():
        logger.info("Background thread: Warming up Match Engine (loading Parakeet model)...")
        get_engine()
        logger.info("Background thread: Match Engine ready!")
        
    threading.Thread(target=warm_up_engine, daemon=True).start()

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
