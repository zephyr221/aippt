import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aippt_api.config import get_settings
from aippt_api.db import reset_engine
from aippt_api.main import create_app


@pytest.fixture()
def app_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AIPPT_DATABASE_URL", f"sqlite:///{tmp_path / 'aippt-test.db'}")
    monkeypatch.setenv("AIPPT_JOBS_ROOT", str(tmp_path / "jobs"))
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
