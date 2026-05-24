from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "AIPPT"
    database_url: str = "sqlite:///./aippt.db"
    session_secret: str = "change-me-in-production"
    session_cookie_name: str = "aippt_session"
    oauth_state_cookie_name: str = "aippt_oauth_state"
    secure_cookies: bool = False
    jobs_root: str = "/srv/aippt/jobs"
    builder_command: str = "aippt-build"
    worker_command_timeout_seconds: int = 120
    jaccount_client_id: str = ""
    jaccount_client_secret: str = ""
    jaccount_redirect_uri: str = "http://127.0.0.1:8000/api/auth/jaccount/callback"
    jaccount_authorize_url: str = "https://jaccount.sjtu.edu.cn/oauth2/authorize"
    jaccount_token_url: str = "https://jaccount.sjtu.edu.cn/oauth2/token"
    jaccount_userinfo_url: str = "https://api.sjtu.edu.cn/v1/me/profile"
    jaccount_scope: str = "basic"
    dev_allow_fake_login: bool = False

    model_config = SettingsConfigDict(env_prefix="AIPPT_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env == "development":
        settings.dev_allow_fake_login = True
    return settings
