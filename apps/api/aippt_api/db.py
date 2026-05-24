from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings


_engine: Engine | None = None
_engine_url: str | None = None


def get_engine() -> Engine:
    global _engine, _engine_url

    settings = get_settings()
    if _engine is None or _engine_url != settings.database_url:
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {},
        )
        _engine_url = settings.database_url
    return _engine


def create_db_and_tables() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _migrate_sqlite_user_table(engine)


def _migrate_sqlite_user_table(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("user")}
    additions = {
        "jaccount": "VARCHAR(64)",
        "code": "VARCHAR(32) NOT NULL DEFAULT ''",
        "affiliation": "VARCHAR NOT NULL DEFAULT ''",
        "user_type": "VARCHAR NOT NULL DEFAULT ''",
        "last_login_at": "DATETIME",
    }

    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in existing_columns:
                connection.execute(text(f'ALTER TABLE "user" ADD COLUMN {column_name} {column_type}'))
        connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_user_jaccount ON "user" (jaccount)'))


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def reset_engine() -> None:
    global _engine, _engine_url

    if _engine is not None:
        _engine.dispose()
    _engine = None
    _engine_url = None
