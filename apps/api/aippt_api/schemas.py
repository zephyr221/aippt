from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .models import DeckStatus, JobStatus, JobType


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    display_name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    jaccount: str | None
    code: str
    email: EmailStr
    display_name: str
    affiliation: str
    user_type: str
    last_login_at: datetime | None
    created_at: datetime


class DeckCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    outline_md: str = ""


class DeckUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    outline_md: str | None = None
    status: DeckStatus | None = None


class DeckRead(BaseModel):
    id: UUID
    owner_user_id: UUID
    title: str
    outline_md: str
    status: DeckStatus
    created_at: datetime
    updated_at: datetime


class JobCreate(BaseModel):
    type: JobType = JobType.BUILD_PPTX
    input_snapshot: str = ""


class JobRead(BaseModel):
    id: UUID
    deck_session_id: UUID
    owner_user_id: UUID
    type: JobType
    status: JobStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
