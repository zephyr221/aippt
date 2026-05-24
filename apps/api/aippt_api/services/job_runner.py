import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlmodel import Session, select

from ..config import Settings
from ..models import DeckSession, DeckStatus, FileAsset, FileKind, Job, JobStatus, JobType
from .workspaces import materialize_job_workspace, write_job_manifest


def run_next_job(session: Session, settings: Settings) -> Job | None:
    job = session.exec(
        select(Job)
        .where(Job.status == JobStatus.QUEUED)
        .order_by(Job.created_at)
    ).first()
    if job is None:
        return None
    return run_job(session, settings, job.id)


def run_job(session: Session, settings: Settings, job_id: UUID) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    deck = session.get(DeckSession, job.deck_session_id)
    if deck is None or deck.owner_user_id != job.owner_user_id:
        raise ValueError(f"Deck not found for job: {job_id}")

    workspace = _workspace_for(settings, deck, job)
    _mark_running(session, deck, job, workspace)

    try:
        if job.type != JobType.BUILD_PPTX:
            raise RuntimeError(f"Unsupported job type: {job.type}")

        outline_path = workspace / "input" / "outline.md"
        deck_ir_path = workspace / "ir" / "deck.json"
        pptx_path = workspace / "out" / "deck.pptx"

        _run_builder(settings, workspace, "outline", outline_path, deck_ir_path, "--title", deck.title)
        _run_builder(settings, workspace, "build", deck_ir_path, pptx_path)

        _add_file_asset(session, deck, FileKind.DECK_IR, deck_ir_path, "application/json")
        _add_file_asset(
            session,
            deck,
            FileKind.PPTX,
            pptx_path,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        _add_file_asset(session, deck, FileKind.LOG, workspace / "logs" / "job.log", "text/plain")

        now = datetime.now(timezone.utc)
        job.status = JobStatus.SUCCEEDED
        job.error_message = None
        job.updated_at = now
        deck.status = DeckStatus.READY
        deck.updated_at = now
        _append_log(workspace, f"{now.isoformat()} succeeded {job.type}")
    except Exception as exc:
        now = datetime.now(timezone.utc)
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
        job.updated_at = now
        deck.status = DeckStatus.FAILED
        deck.updated_at = now
        _append_log(workspace, f"{now.isoformat()} failed {job.type}: {exc}")

    write_job_manifest(workspace, deck, job)
    session.add(deck)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _workspace_for(settings: Settings, deck: DeckSession, job: Job) -> Path:
    if job.workspace_path:
        workspace = Path(job.workspace_path)
        if workspace.exists():
            return workspace

    workspace = materialize_job_workspace(settings, deck, job)
    job.workspace_path = str(workspace)
    return workspace


def _mark_running(session: Session, deck: DeckSession, job: Job, workspace: Path) -> None:
    now = datetime.now(timezone.utc)
    job.status = JobStatus.RUNNING
    job.updated_at = now
    deck.status = DeckStatus.GENERATING
    deck.updated_at = now
    _append_log(workspace, f"{now.isoformat()} running {job.type}")
    write_job_manifest(workspace, deck, job)
    session.add(deck)
    session.add(job)
    session.commit()
    session.refresh(job)


def _run_builder(
    settings: Settings,
    workspace: Path,
    subcommand: str,
    *args: Path | str,
) -> None:
    command = [*shlex.split(settings.builder_command), subcommand, *[str(arg) for arg in args]]
    result = subprocess.run(
        command,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=settings.worker_command_timeout_seconds,
        check=False,
    )
    if result.stdout:
        _append_log(workspace, result.stdout.strip())
    if result.stderr:
        _append_log(workspace, result.stderr.strip())
    if result.returncode != 0:
        raise RuntimeError(f"Builder command failed ({result.returncode}): {' '.join(command)}")


def _add_file_asset(
    session: Session,
    deck: DeckSession,
    kind: FileKind,
    path: Path,
    content_type: str,
) -> None:
    asset = FileAsset(
        owner_user_id=deck.owner_user_id,
        deck_session_id=deck.id,
        kind=kind,
        storage_path=str(path),
        content_type=content_type,
    )
    session.add(asset)


def _append_log(workspace: Path, line: str) -> None:
    log_path = workspace / "logs" / "job.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")
