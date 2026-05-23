import json
from pathlib import Path

from ..config import Settings
from ..models import DeckSession, Job


WORKSPACE_DIRS = ("input", "ir", "skill", "assets", "scripts", "out", "logs")


def job_workspace_path(settings: Settings, job: Job) -> Path:
    return Path(settings.jobs_root) / str(job.owner_user_id) / str(job.id)


def materialize_job_workspace(settings: Settings, deck: DeckSession, job: Job) -> Path:
    workspace = job_workspace_path(settings, job)
    workspace.mkdir(parents=True, exist_ok=False)
    for dirname in WORKSPACE_DIRS:
        (workspace / dirname).mkdir()

    outline = job.input_snapshot or deck.outline_md or ""
    (workspace / "input" / "outline.md").write_text(_normalize_text(outline), encoding="utf-8")
    (workspace / "manifest.json").write_text(
        json.dumps(_manifest(deck, job), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text(_agent_instructions(deck, job), encoding="utf-8")
    (workspace / "logs" / "job.log").write_text(
        f"{job.created_at.isoformat()} queued {job.type}\n",
        encoding="utf-8",
    )
    return workspace


def _manifest(deck: DeckSession, job: Job) -> dict[str, str]:
    return {
        "schema_version": "1",
        "job_id": str(job.id),
        "deck_session_id": str(deck.id),
        "owner_user_id": str(job.owner_user_id),
        "job_type": job.type,
        "status": job.status,
        "deck_title": deck.title,
        "created_at": job.created_at.isoformat(),
        "input_outline": "input/outline.md",
        "deck_ir": "ir/deck.json",
        "pptx_output": "out/deck.pptx",
        "log_file": "logs/job.log",
    }


def _agent_instructions(deck: DeckSession, job: Job) -> str:
    return f"""# AIPPT Job Workspace

Deck: {deck.title}
Job: {job.id}
Type: {job.type}

## Boundaries

- Work only inside this workspace.
- Read user input from `input/outline.md`.
- Write Deck IR to `ir/deck.json`.
- Write build output to `out/deck.pptx`.
- Write diagnostics to `logs/job.log`.
- Do not read secrets, global app state, or other job directories.
- Do not install dependencies at runtime.

## Builder Contract

The deterministic builder accepts the constrained Deck IR schema from
`aippt_builder.schema.Deck`. Validation must pass before PPTX generation.
"""


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return text if text.endswith("\n") else f"{text}\n"
