import sys
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routers import admin, kids, sessions, problems

app = FastAPI(title="מתמטיקה לילדים", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kids.router)
app.include_router(sessions.router)
app.include_router(problems.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    log_dir = Path("data/logs")
    log_dir.mkdir(exist_ok=True)
    logger.remove()
    logger.add(sys.stdout, format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")
    logger.add(
        str(log_dir / "math-tutor.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        rotation="10 MB",
        retention="7 days"
    )
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
