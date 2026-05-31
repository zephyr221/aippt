import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth import get_current_user
from ..db import get_session
from ..models import DeckSession, User
from ..schemas import DeckCreate, DeckRead, DeckUpdate


router = APIRouter()


@router.get("", response_model=list[DeckRead])
def list_decks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[DeckSession]:
    return list(
        session.exec(
            select(DeckSession)
            .where(DeckSession.owner_user_id == current_user.id)
            .order_by(DeckSession.updated_at.desc())
        )
    )


@router.post("", response_model=DeckRead, status_code=status.HTTP_201_CREATED)
def create_deck(
    payload: DeckCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DeckSession:
    deck = DeckSession(
        owner_user_id=current_user.id,
        title=payload.title,
        outline_md=payload.outline_md,
    )
    session.add(deck)
    session.commit()
    session.refresh(deck)
    return deck


@router.get("/{deck_id}", response_model=DeckRead)
def get_deck(
    deck_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DeckSession:
    deck = session.exec(
        select(DeckSession).where(
            DeckSession.id == deck_id,
            DeckSession.owner_user_id == current_user.id,
        )
    ).first()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


@router.get("/{deck_id}/outline")
def get_deck_outline(
    deck_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    deck = session.exec(
        select(DeckSession).where(
            DeckSession.id == deck_id,
            DeckSession.owner_user_id == current_user.id,
        )
    ).first()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")

    markdown = deck.outline_md or ""
    pages = _outline_pages(markdown)
    return {
        "deck": {
            "id": str(deck.id),
            "title": deck.title,
            "status": deck.status.value,
            "created_at": deck.created_at.isoformat(),
            "updated_at": deck.updated_at.isoformat(),
        },
        "markdown": markdown,
        "pages": pages,
        "page_count": len(pages),
    }


@router.patch("/{deck_id}", response_model=DeckRead)
def update_deck(
    deck_id: UUID,
    payload: DeckUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DeckSession:
    deck = session.exec(
        select(DeckSession).where(
            DeckSession.id == deck_id,
            DeckSession.owner_user_id == current_user.id,
        )
    ).first()
    if deck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(deck, key, value)
    deck.updated_at = datetime.now(timezone.utc)
    session.add(deck)
    session.commit()
    session.refresh(deck)
    return deck


_PAGE_HEADING_RE = re.compile(r"^##\s*第\s*(\d+)\s*页\s*(?:[·:：\-.—]\s*)?(.*)$", re.MULTILINE)


def _outline_pages(markdown: str) -> list[dict[str, Any]]:
    text = markdown.strip()
    if not text:
        return []

    matches = list(_PAGE_HEADING_RE.finditer(text))
    if not matches:
        heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = heading.group(1).strip() if heading else "创作需求"
        return [{"number": 1, "title": title, "markdown": text}]

    pages: list[dict[str, Any]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        number = int(match.group(1))
        title = (match.group(2) or "").strip() or f"第 {number} 页"
        pages.append(
            {
                "number": number,
                "title": title,
                "markdown": text[start:end].strip(),
            }
        )
    return pages
