from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from ..auth import get_current_user
from ..db import get_session
from ..models import DeckSession, FileAsset, User
from ..schemas import FileRead


router = APIRouter()


@router.get("/decks/{deck_id}", response_model=list[FileRead])
def list_deck_files(
    deck_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[FileAsset]:
    deck = _get_owned_deck(session, deck_id, current_user)
    return list(
        session.exec(
            select(FileAsset)
            .where(
                FileAsset.deck_session_id == deck.id,
                FileAsset.owner_user_id == current_user.id,
            )
            .order_by(FileAsset.created_at.desc())
        )
    )


@router.get("/{file_id}/download")
def download_file(
    file_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    asset = session.exec(
        select(FileAsset).where(
            FileAsset.id == file_id,
            FileAsset.owner_user_id == current_user.id,
        )
    ).first()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    deck = _get_owned_deck(session, asset.deck_session_id, current_user)
    path = Path(asset.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")

    filename = _download_filename(deck, asset, path)
    return FileResponse(path, media_type=asset.content_type, filename=filename)


def _get_owned_deck(session: Session, deck_id: UUID, current_user: User) -> DeckSession:
    deck = session.exec(
        select(DeckSession).where(
            DeckSession.id == deck_id,
            DeckSession.owner_user_id == current_user.id,
        )
    ).first()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


def _download_filename(deck: DeckSession, asset: FileAsset, path: Path) -> str:
    title = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in deck.title.strip())
    title = "-".join(part for part in title.split("-") if part) or "deck"
    suffix = path.suffix or _default_suffix(asset)
    return f"{title}-{asset.kind.value}{suffix}"


def _default_suffix(asset: FileAsset) -> str:
    if asset.content_type == "application/json":
        return ".json"
    if asset.content_type == "text/plain":
        return ".txt"
    if asset.kind.value == "pptx":
        return ".pptx"
    return ""
