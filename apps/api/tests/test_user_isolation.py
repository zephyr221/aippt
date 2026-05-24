import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from aippt_api.config import get_settings
from aippt_api.db import get_engine, reset_engine
from aippt_api.main import create_app
from aippt_api.models import DeckSession, DeckStatus, FileAsset, FileKind, JobStatus
from aippt_api.services.job_runner import run_next_job


@pytest.fixture()
def app_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AIPPT_DATABASE_URL", f"sqlite:///{tmp_path / 'aippt-test.db'}")
    monkeypatch.setenv("AIPPT_JOBS_ROOT", str(tmp_path / "jobs"))
    monkeypatch.setenv("AIPPT_JACCOUNT_CLIENT_ID", "test-client")
    monkeypatch.setenv("AIPPT_JACCOUNT_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv(
        "AIPPT_JACCOUNT_REDIRECT_URI",
        "http://testserver/api/auth/jaccount/callback",
    )
    monkeypatch.setenv(
        "AIPPT_BUILDER_COMMAND",
        os.environ.get("AIPPT_BUILDER_COMMAND", f"{sys.executable} -m aippt_builder.cli"),
    )
    get_settings.cache_clear()
    reset_engine()
    yield create_app(), tmp_path
    reset_engine()
    get_settings.cache_clear()


def register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password-123", "display_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    return response.json()


def test_root_redirect_respects_proxy_root_path(app_context) -> None:
    app, _tmp_path = app_context
    with TestClient(app, root_path="/ppt") as client:
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ppt/docs"


def test_users_only_see_their_own_decks(app_context) -> None:
    app, _tmp_path = app_context
    with TestClient(app) as alice, TestClient(app) as bob:
        register(alice, "alice@example.com")
        register(bob, "bob@example.com")

        alice_deck = alice.post("/api/decks", json={"title": "Alice Deck", "outline_md": "# A"})
        assert alice_deck.status_code == 201
        deck_id = alice_deck.json()["id"]

        bob_list = bob.get("/api/decks")
        assert bob_list.status_code == 200
        assert bob_list.json() == []

        bob_get = bob.get(f"/api/decks/{deck_id}")
        assert bob_get.status_code == 404


def test_jaccount_dev_login_creates_session(app_context) -> None:
    app, _tmp_path = app_context
    with TestClient(app) as client:
        response = client.get(
            "/api/auth/jaccount/login?dev_login=alice&next=/decks",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/decks"

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        payload = me.json()
        assert payload["jaccount"] == "alice"
        assert payload["display_name"] == "开发用户 alice"
        assert payload["user_type"] == "student"


def test_jaccount_login_redirect_sets_signed_state(app_context) -> None:
    app, _tmp_path = app_context
    with TestClient(app) as client:
        response = client.get("/api/auth/jaccount/login?next=/decks", follow_redirects=False)
        assert response.status_code == 302
        location = response.headers["location"]
        parsed = urlparse(location)
        query = parse_qs(parsed.query)

        assert location.startswith("https://jaccount.sjtu.edu.cn/oauth2/authorize?")
        assert query["client_id"] == ["test-client"]
        assert query["redirect_uri"] == ["http://testserver/api/auth/jaccount/callback"]
        assert query["scope"] == ["basic"]
        assert query["response_type"] == ["code"]
        assert query["state"][0]
        assert "aippt_oauth_state" in client.cookies


def test_jaccount_callback_upserts_profile_user(app_context, monkeypatch: pytest.MonkeyPatch) -> None:
    app, _tmp_path = app_context

    class FakeJaccountClient:
        def __init__(self, timeout: int) -> None:
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def post(self, _url: str, *, data: dict, headers: dict) -> httpx.Response:
            assert data["code"] == "abc"
            assert data["client_id"] == "test-client"
            assert headers["Accept"] == "application/json"
            return httpx.Response(200, json={"access_token": "token-123"})

        def get(self, _url: str, *, headers: dict) -> httpx.Response:
            assert headers["Authorization"] == "Bearer token-123"
            return httpx.Response(
                200,
                json={
                    "errno": 0,
                    "entities": [
                        {
                            "account": "moran",
                            "code": "001",
                            "name": "Moran",
                            "email": "moran@sjtu.edu.cn",
                            "userType": "faculty",
                            "organize": {"name": "SJTU"},
                        }
                    ],
                },
            )

    monkeypatch.setattr("aippt_api.routes.auth.httpx.Client", FakeJaccountClient)

    with TestClient(app) as client:
        login_response = client.get("/api/auth/jaccount/login?next=/decks", follow_redirects=False)
        state = parse_qs(urlparse(login_response.headers["location"]).query)["state"][0]

        callback_response = client.get(
            f"/api/auth/jaccount/callback?code=abc&state={state}",
            follow_redirects=False,
        )
        assert callback_response.status_code == 302
        assert callback_response.headers["location"] == "/decks"

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["jaccount"] == "moran"
        assert me.json()["display_name"] == "Moran"
        assert me.json()["affiliation"] == "SJTU"
        assert me.json()["user_type"] == "faculty"


def test_existing_sqlite_user_table_gets_jaccount_columns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'legacy.db'}"
    legacy_engine = create_engine(database_url)
    with legacy_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE "user" (
                    id CHAR(32) NOT NULL PRIMARY KEY,
                    email VARCHAR NOT NULL,
                    display_name VARCHAR NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        connection.execute(text('CREATE UNIQUE INDEX ix_user_email ON "user" (email)'))

    monkeypatch.setenv("AIPPT_DATABASE_URL", database_url)
    get_settings.cache_clear()
    reset_engine()

    try:
        with TestClient(create_app()) as client:
            response = client.get(
                "/api/auth/jaccount/login?dev_login=legacy&next=/decks",
                follow_redirects=False,
            )
            assert response.status_code == 302
            assert response.headers["location"] == "/decks"

            me = client.get("/api/auth/me")
            assert me.status_code == 200
            assert me.json()["jaccount"] == "legacy"
    finally:
        reset_engine()
        get_settings.cache_clear()


def test_job_creation_materializes_owner_scoped_workspace(app_context) -> None:
    app, tmp_path = app_context
    with TestClient(app) as alice, TestClient(app) as bob:
        alice_user = register(alice, "alice@example.com")
        register(bob, "bob@example.com")

        alice_deck = alice.post(
            "/api/decks",
            json={"title": "Alice Deck", "outline_md": "# Alice Deck\n\n- First point"},
        )
        assert alice_deck.status_code == 201
        deck_id = alice_deck.json()["id"]

        response = alice.post(f"/api/jobs/decks/{deck_id}", json={"type": "build_pptx"})
        assert response.status_code == 201
        job = response.json()
        assert "workspace_path" not in job
        assert job["status"] == "queued"

        workspace = tmp_path / "jobs" / alice_user["id"] / job["id"]
        assert (workspace / "AGENTS.md").is_file()
        assert (workspace / "input" / "outline.md").read_text(encoding="utf-8") == (
            "# Alice Deck\n\n- First point\n"
        )
        assert (workspace / "logs" / "job.log").is_file()

        manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["job_id"] == job["id"]
        assert manifest["deck_session_id"] == deck_id
        assert manifest["owner_user_id"] == alice_user["id"]
        assert manifest["input_outline"] == "input/outline.md"
        assert manifest["pptx_output"] == "out/deck.pptx"

        alice_jobs = alice.get(f"/api/jobs/decks/{deck_id}")
        assert alice_jobs.status_code == 200
        assert [item["id"] for item in alice_jobs.json()] == [job["id"]]

        bob_create = bob.post(f"/api/jobs/decks/{deck_id}", json={"type": "build_pptx"})
        assert bob_create.status_code == 404
        bob_list = bob.get(f"/api/jobs/decks/{deck_id}")
        assert bob_list.status_code == 404
        bob_get = bob.get(f"/api/jobs/{job['id']}")
        assert bob_get.status_code == 404

        deck_after_job = alice.get(f"/api/decks/{deck_id}")
        assert deck_after_job.status_code == 200
        assert deck_after_job.json()["status"] == "generating"


def test_worker_run_once_builds_pptx_and_records_artifacts(app_context) -> None:
    app, tmp_path = app_context
    with TestClient(app) as alice:
        register(alice, "alice@example.com")
        deck_response = alice.post(
            "/api/decks",
            json={
                "title": "AIPPT Demo",
                "outline_md": "# AIPPT Demo\n\n## 目标\n\n- 多用户隔离\n- 自动生成 PPTX",
            },
        )
        assert deck_response.status_code == 201
        deck_id = deck_response.json()["id"]

        job_response = alice.post(f"/api/jobs/decks/{deck_id}", json={"type": "build_pptx"})
        assert job_response.status_code == 201
        job_id = job_response.json()["id"]

    with Session(get_engine()) as session:
        job = run_next_job(session, get_settings())
        assert job is not None
        assert str(job.id) == job_id
        assert job.status == JobStatus.SUCCEEDED

        deck = session.get(DeckSession, UUID(deck_id))
        assert deck is not None
        assert deck.status == DeckStatus.READY

        assets = session.exec(
            select(FileAsset).where(FileAsset.deck_session_id == deck.id)
        ).all()
        kinds = {asset.kind for asset in assets}
        assert {FileKind.DECK_IR, FileKind.PPTX, FileKind.LOG}.issubset(kinds)

    job_workspace = next((tmp_path / "jobs").glob(f"*/{job_id}"))
    assert (job_workspace / "ir" / "deck.json").is_file()
    assert (job_workspace / "out" / "deck.pptx").stat().st_size > 0
    log_text = (job_workspace / "logs" / "job.log").read_text(encoding="utf-8")
    assert "running build_pptx" in log_text
    assert "succeeded build_pptx" in log_text
