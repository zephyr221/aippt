from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeckStatus(StrEnum):
    DRAFT = "draft"
    OUTLINE_READY = "outline_ready"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class JobType(StrEnum):
    PLAN_OUTLINE = "plan_outline"
    BUILD_PPTX = "build_pptx"
    REPAIR_IR = "repair_ir"


class FileKind(StrEnum):
    OUTLINE = "outline"
    DECK_IR = "deck_ir"
    PPTX = "pptx"
    PREVIEW = "preview"
    LOG = "log"


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    jaccount: str | None = Field(default=None, index=True, unique=True, max_length=64)
    code: str = Field(default="", max_length=32)
    email: str = Field(index=True, unique=True)
    display_name: str
    password_hash: str = ""
    affiliation: str = ""
    user_type: str = ""
    last_login_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    decks: list["DeckSession"] = Relationship(back_populates="owner")


class DeckSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str = Field(default="Untitled Deck", max_length=160)
    outline_md: str = ""
    status: DeckStatus = Field(default=DeckStatus.DRAFT, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    owner: User = Relationship(back_populates="decks")
    jobs: list["Job"] = Relationship(back_populates="deck")
    files: list["FileAsset"] = Relationship(back_populates="deck")


class Job(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    deck_session_id: UUID = Field(foreign_key="decksession.id", index=True)
    owner_user_id: UUID = Field(foreign_key="user.id", index=True)
    type: JobType = Field(index=True)
    status: JobStatus = Field(default=JobStatus.QUEUED, index=True)
    workspace_path: str | None = None
    input_snapshot: str = ""
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    deck: DeckSession = Relationship(back_populates="jobs")


class FileAsset(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_user_id: UUID = Field(foreign_key="user.id", index=True)
    deck_session_id: UUID = Field(foreign_key="decksession.id", index=True)
    kind: FileKind = Field(index=True)
    storage_path: str
    content_type: str = "application/octet-stream"
    created_at: datetime = Field(default_factory=utcnow)

    deck: DeckSession = Relationship(back_populates="files")
