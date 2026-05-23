from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth import get_current_user
from ..config import Settings, get_settings
from ..db import get_session
from ..models import DeckSession, Job, User
from ..schemas import JobCreate, JobRead


router = APIRouter()


@router.post("/decks/{deck_id}", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    deck_id: UUID,
    payload: JobCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Job:
    deck = session.exec(
        select(DeckSession).where(
            DeckSession.id == deck_id,
            DeckSession.owner_user_id == current_user.id,
        )
    ).first()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")

    job = Job(
        deck_session_id=deck.id,
        owner_user_id=current_user.id,
        type=payload.type,
        input_snapshot=payload.input_snapshot or deck.outline_md,
    )
    workspace = Path(settings.jobs_root) / str(job.id)
    job.workspace_path = str(workspace)
    deck.updated_at = datetime.now(timezone.utc)

    session.add(job)
    session.add(deck)
    session.commit()
    session.refresh(job)
    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Job:
    job = session.exec(
        select(Job).where(
            Job.id == job_id,
            Job.owner_user_id == current_user.id,
        )
    ).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

