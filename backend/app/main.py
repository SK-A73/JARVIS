"""
JARVIS Core Backend Gateway Application
High-performance asynchronous core powering 24/7 tasks, WebSocket mesh, and REST APIs.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.database import init_db
from backend.app.agent.task_queue import TaskQueue
from backend.app.api.auth_router import router as auth_router
from backend.app.api.memory_router import router as memory_router
from backend.app.api.task_router import router as task_router
from backend.app.api.ws_router import router as ws_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database and Start 24/7 Task Queue
    init_db()
    task_queue = TaskQueue.get_instance()
    task_queue.start_worker()
    yield
    # Shutdown: Clean up task workers
    task_queue.stop_worker()

app = FastAPI(
    title="JARVIS Autonomous Personal AI Assistant",
    description="Multi-device AI Assistant Core for Android, Laptop, and Cloud",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for cross-origin clients (Android emulator, web dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(task_router)
app.include_router(ws_router)

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "JARVIS Personal AI Assistant",
        "environment": settings.JARVIS_ENV,
        "default_llm_provider": settings.DEFAULT_LLM_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.JARVIS_HOST, port=settings.JARVIS_PORT, reload=True)
