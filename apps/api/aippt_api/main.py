from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import create_db_and_tables
from .routes import auth, decks, files, health, jobs, ui


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AIPPT API", lifespan=lifespan)
    app.include_router(ui.router, tags=["ui"])
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(decks.router, prefix="/api/decks", tags=["decks"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(files.router, prefix="/api/files", tags=["files"])
    return app


app = create_app()
