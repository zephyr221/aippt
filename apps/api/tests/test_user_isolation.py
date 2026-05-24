import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
import httpx
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from aippt_api.config import get_settings
from aippt_api.db import get_engine, reset_engine
from aippt_api.main import create_app
from aippt_api.models import DeckSession, DeckStatus, FileAsset, FileKind, JobStatus
from aippt_api.services.job_runner import run_next_job
from aippt_api.services.preview import _write_contact_sheet


@pytest.fixture()
def app_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AIPPT_DATABASE_URL", f"sqlite:///{tmp_path / 'aippt-test.db'}")
    monkeypatch.setenv("AIPPT_JOBS_ROOT", str(tmp_path / "jobs"))
    monkeypatch.setenv(
        "AIPPT_TEMPLATE_PPTX_PATH",
        str(Path(__file__).resolve().parents[3] / "docs" / "SJTU PPT 模板" / "SJTU 模板.pptx"),
    )
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
        response = client.get("/")
        assert response.status_code == 200
        assert 'data-root-path="/ppt"' in response.text
        assert "AI PPT 生成工作台" in response.text
        assert "生成 PPT" in response.text
        assert "快速生成 PPTX" not in response.text


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


def test_password_auth_is_disabled_in_production(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIPPT_APP_ENV", "production")
    monkeypatch.setenv("AIPPT_DATABASE_URL", f"sqlite:///{tmp_path / 'prod-auth.db'}")
    get_settings.cache_clear()
    reset_engine()

    try:
        with TestClient(create_app()) as client:
            register_response = client.post(
                "/api/auth/register",
                json={
                    "email": "prod@example.com",
                    "password": "password-123",
                    "display_name": "prod",
                },
            )
            assert register_response.status_code == 404

            login_response = client.post(
                "/api/auth/login",
                json={"email": "prod@example.com", "password": "password-123"},
            )
            assert login_response.status_code == 404
    finally:
        reset_engine()
        get_settings.cache_clear()


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
    with TestClient(app) as alice, TestClient(app) as bob:
        register(alice, "alice@example.com")
        register(bob, "bob@example.com")
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

        files_response = alice.get(f"/api/files/decks/{deck_id}")
        assert files_response.status_code == 200
        files = files_response.json()
        pptx_file = next(file for file in files if file["kind"] == "pptx")

        download_response = alice.get(f"/api/files/{pptx_file['id']}/download")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        assert download_response.content.startswith(b"PK")

        assert bob.get(f"/api/files/decks/{deck_id}").status_code == 404
        assert bob.get(f"/api/files/{pptx_file['id']}/download").status_code == 404

    job_workspace = next((tmp_path / "jobs").glob(f"*/{job_id}"))
    assert (job_workspace / "ir" / "deck.json").is_file()
    assert (job_workspace / "out" / "deck.pptx").stat().st_size > 0
    log_text = (job_workspace / "logs" / "job.log").read_text(encoding="utf-8")
    assert "running build_pptx" in log_text
    assert "succeeded build_pptx" in log_text


def test_worker_expands_brief_prompt_to_intro_deck(app_context) -> None:
    app, tmp_path = app_context
    with TestClient(app) as alice:
        register(alice, "alice@example.com")
        deck_response = alice.post(
            "/api/decks",
            json={
                "title": "机器学习科普",
                "outline_md": "请制作五六页 PPT，关于机器学习的科普啊",
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
            assert job.status == JobStatus.SUCCEEDED

    job_workspace = next((tmp_path / "jobs").glob(f"*/{job_id}"))
    deck_ir = json.loads((job_workspace / "ir" / "deck.json").read_text(encoding="utf-8"))
    assert deck_ir["title"] == "机器学习科普"
    assert len(deck_ir["slides"]) == 6
    assert [slide["title"] for slide in deck_ir["slides"][1:5]] == [
        "为什么值得了解",
        "核心概念",
        "它如何工作",
        "身边的应用",
    ]


def test_worker_hermes_plan_updates_outline_and_records_artifact(
    app_context,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, tmp_path = app_context
    fake_hermes = tmp_path / "fake-hermes"
    fake_hermes.write_text(
        """#!/usr/bin/env bash
cat <<'EOF'
# 机器学习科普

> 深度规划版：用 6 页讲清楚机器学习是什么、如何工作、怎样判断边界。

## 第 1 页 · 封面
主标题：机器学习科普
副标题：从数据规律到现实应用

## 第 2 页 · 为什么值得了解
机器学习已经进入学习、工作和科研工具链，关键是理解它能做什么。
- 技术位置：它不再只是实验室概念，搜索、推荐、图像识别和语音转写都在使用。
- 学习价值：它让计算机从历史样本中总结规律，适合处理规则难以手写的问题。
- 使用边界：结果依赖数据质量和任务定义，上线后仍需要新样本验证和人工反馈。

## 第 3 页 · 它如何工作
典型流程是数据准备、模型训练、效果评估和迭代改进。
- 数据准备：收集样本并清洗异常值，把输入表示为特征 x。
- 模型训练：用 ŷ=fθ(x) 产生预测，根据误差调整参数 θ。
- 公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))，训练就是让 J(θ) 变小。

## 第 4 页 · 身边的应用
机器学习常嵌入具体流程，帮助人更快发现、判断和生成。
- 学习场景：根据练习记录推荐下一道题，识别知识薄弱点。
- 科研场景：从实验和模拟数据中发现模式，辅助筛选候选方案。
- 办公场景：自动摘要、分类、检索和内容生成降低重复劳动。
EOF
""",
        encoding="utf-8",
    )
    fake_hermes.chmod(0o755)
    monkeypatch.setenv("AIPPT_HERMES_PLANNER_ENABLED", "true")
    monkeypatch.setenv("AIPPT_HERMES_COMMAND", str(fake_hermes))
    monkeypatch.setenv("AIPPT_HERMES_PROVIDER", "xiaomi")
    monkeypatch.setenv("AIPPT_HERMES_MODEL", "mimo-v2.5-pro")
    get_settings.cache_clear()

    with TestClient(app) as alice:
        register(alice, "alice@example.com")
        deck_response = alice.post(
            "/api/decks",
            json={
                "title": "机器学习科普",
                "outline_md": "请制作五六页 PPT，关于机器学习的科普啊",
            },
        )
        assert deck_response.status_code == 201
        deck_id = deck_response.json()["id"]

        job_response = alice.post(f"/api/jobs/decks/{deck_id}", json={"type": "plan_outline"})
        assert job_response.status_code == 201
        job_id = job_response.json()["id"]
        assert alice.get(f"/api/decks/{deck_id}").json()["status"] == "generating"

        with Session(get_engine()) as session:
            job = run_next_job(session, get_settings())
            assert job is not None
            assert str(job.id) == job_id
            assert job.status == JobStatus.SUCCEEDED

            deck = session.get(DeckSession, UUID(deck_id))
            assert deck is not None
            assert deck.status == DeckStatus.OUTLINE_READY
            assert "深度规划版" in deck.outline_md
            assert "一句话" not in deck.outline_md
            assert "请制作五六页" not in deck.outline_md

            assets = session.exec(
                select(FileAsset).where(FileAsset.deck_session_id == deck.id)
            ).all()
            kinds = {asset.kind for asset in assets}
            assert FileKind.OUTLINE in kinds
            assert FileKind.PPTX not in kinds

        files_response = alice.get(f"/api/files/decks/{deck_id}")
        assert files_response.status_code == 200
        outline_file = next(file for file in files_response.json() if file["kind"] == "outline")
        download_response = alice.get(f"/api/files/{outline_file['id']}/download")
        assert download_response.status_code == 200
        assert "深度规划版" in download_response.text
        assert "一句话" not in download_response.text
        log_response = alice.get(f"/api/jobs/{job_id}/log")
        assert log_response.status_code == 200
        assert "succeeded plan_outline" in log_response.json()["log_text"]

    job_workspace = next((tmp_path / "jobs").glob(f"*/{job_id}"))
    assert (job_workspace / "ir" / "planned_outline.md").is_file()
    assert (job_workspace / "logs" / "hermes_plan.md").is_file()
    plan_log = (job_workspace / "logs" / "job.log").read_text(encoding="utf-8")
    assert "running plan_outline" in plan_log
    assert "succeeded plan_outline" in plan_log


def test_worker_hermes_review_writes_non_destructive_report(app_context) -> None:
    app, tmp_path = app_context
    with TestClient(app) as alice, TestClient(app) as bob:
        register(alice, "alice@example.com")
        register(bob, "bob@example.com")
        deck_response = alice.post(
            "/api/decks",
            json={
                "title": "AI × 计算材料科研",
                "outline_md": (
                    "# AI × 计算材料科研\n\n"
                    "## 第 1 页 · 封面\n\n"
                    "**AI × 计算材料科研**\n\n"
                    "## 第 2 页 · 开场：一个事实\n\n"
                    "- 2026.03.23 — Claude 自主完成 Boltzmann solver\n"
                    "- Agent 工作流需要记忆和验证闭环\n"
                ),
            },
        )
        assert deck_response.status_code == 201
        deck_id = deck_response.json()["id"]

        build_response = alice.post(f"/api/jobs/decks/{deck_id}", json={"type": "build_pptx"})
        assert build_response.status_code == 201
        with Session(get_engine()) as session:
            build_job = run_next_job(session, get_settings())
            assert build_job is not None
            assert build_job.status == JobStatus.SUCCEEDED

        review_response = alice.post(f"/api/jobs/decks/{deck_id}", json={"type": "hermes_review"})
        assert review_response.status_code == 201
        review_job_id = review_response.json()["id"]

        deck_after_review_create = alice.get(f"/api/decks/{deck_id}")
        assert deck_after_review_create.status_code == 200
        assert deck_after_review_create.json()["status"] == "ready"

        with Session(get_engine()) as session:
            review_job = run_next_job(session, get_settings())
            assert review_job is not None
            assert str(review_job.id) == review_job_id
            assert review_job.status == JobStatus.SUCCEEDED

            deck = session.get(DeckSession, UUID(deck_id))
            assert deck is not None
            assert deck.status == DeckStatus.READY

            assets = session.exec(
                select(FileAsset).where(FileAsset.deck_session_id == deck.id)
            ).all()
            kinds = {asset.kind for asset in assets}
            assert FileKind.REVIEW in kinds

        files_response = alice.get(f"/api/files/decks/{deck_id}")
        assert files_response.status_code == 200
        review_file = next(file for file in files_response.json() if file["kind"] == "review")
        download_response = alice.get(f"/api/files/{review_file['id']}/download")
        assert download_response.status_code == 200
        assert b"Hermes PPT Review" in download_response.content
        assert "Agent" in download_response.text

        assert bob.get(f"/api/files/{review_file['id']}/download").status_code == 404

    review_workspace = next((tmp_path / "jobs").glob(f"*/{review_job_id}"))
    assert (review_workspace / "qa" / "qa.json").is_file()
    qa = json.loads((review_workspace / "qa" / "qa.json").read_text(encoding="utf-8"))
    assert qa["preview"]["enabled"] is True
    assert "contact_sheet_rendered" in qa["preview"]
    assert (review_workspace / "logs" / "hermes_review.md").is_file()
    assert "## Preview QA" in (review_workspace / "logs" / "hermes_review.md").read_text(
        encoding="utf-8"
    )
    review_log = (review_workspace / "logs" / "job.log").read_text(encoding="utf-8")
    assert "running hermes_review" in review_log
    assert "succeeded hermes_review" in review_log


def test_contact_sheet_renderer_creates_png(tmp_path: Path) -> None:
    page_paths: list[Path] = []
    for index, color in enumerate(((166, 32, 56), (197, 164, 108), (40, 48, 64)), start=1):
        path = tmp_path / f"slide-{index:02d}.png"
        Image.new("RGB", (640, 360), color).save(path)
        page_paths.append(path)

    output_path = tmp_path / "contact-sheet.png"
    _write_contact_sheet(tuple(page_paths), output_path, 240)

    assert output_path.is_file()
    with Image.open(output_path) as image:
        assert image.width > 240
        assert image.height > 180
