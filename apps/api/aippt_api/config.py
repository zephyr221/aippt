from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AIPPT"
    database_url: str = "sqlite:///./aippt.db"
    session_secret: str = "change-me-in-production"
    session_cookie_name: str = "aippt_session"
    secure_cookies: bool = False
    jobs_root: str = "/srv/aippt/jobs"
    builder_command: str = "aippt-build"
    worker_command_timeout_seconds: int = 120

    model_config = SettingsConfigDict(env_prefix="AIPPT_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
