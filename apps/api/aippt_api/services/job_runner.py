import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import update
from sqlmodel import Session, select

from ..config import Settings
from ..models import DeckSession, DeckStatus, FileAsset, FileKind, Job, JobStatus, JobType
from .hermes_planner import write_hermes_plan
from .hermes_review import write_hermes_review
from .preview import build_preview_artifacts
from .workspaces import materialize_job_workspace, write_job_manifest


def run_next_job(session: Session, settings: Settings) -> Job | None:
    job_ids = session.exec(
        select(Job.id)
        .where(Job.status == JobStatus.QUEUED)
        .order_by(Job.created_at)
        .limit(10)
    ).all()
    for job_id in job_ids:
        if _claim_job(session, job_id):
            return run_job(session, settings, job_id)
    return None


def run_job(session: Session, settings: Settings, job_id: UUID) -> Job:
    job = session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    deck = session.get(DeckSession, job.deck_session_id)
    if deck is None or deck.owner_user_id != job.owner_user_id:
        raise ValueError(f"Deck not found for job: {job_id}")

    if job.status == JobStatus.QUEUED and not _claim_job(session, job.id):
        raise RuntimeError(f"Job was already claimed by another worker: {job_id}")
    if job.status not in {JobStatus.QUEUED, JobStatus.RUNNING}:
        raise RuntimeError(f"Job is not runnable: {job_id} ({job.status})")

    workspace = _workspace_for(settings, deck, job)
    _mark_running(session, deck, job, workspace)
    enqueued_followup = False

    try:
        if job.type == JobType.BUILD_PPTX:
            _run_build_pptx(session, settings, deck, workspace)
        elif job.type == JobType.PLAN_OUTLINE:
            enqueued_followup = _run_plan_outline(session, settings, deck, job, workspace)
        elif job.type == JobType.HERMES_REVIEW:
            _run_hermes_review(session, settings, deck, workspace)
        else:
            raise RuntimeError(f"Unsupported job type: {job.type}")

        now = datetime.now(timezone.utc)
        job.status = JobStatus.SUCCEEDED
        job.error_message = None
        job.updated_at = now
        if _job_updates_deck_status(job):
            if job.type == JobType.PLAN_OUTLINE:
                deck.status = DeckStatus.GENERATING if enqueued_followup else DeckStatus.OUTLINE_READY
            else:
                deck.status = DeckStatus.READY
        deck.updated_at = now
        _append_log(workspace, f"{now.isoformat()} succeeded {job.type}")
    except Exception as exc:
        now = datetime.now(timezone.utc)
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
        job.updated_at = now
        if _job_updates_deck_status(job):
            deck.status = DeckStatus.FAILED
        deck.updated_at = now
        _append_log(workspace, f"{now.isoformat()} failed {job.type}: {exc}")

    write_job_manifest(workspace, deck, job)
    session.add(deck)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _claim_job(session: Session, job_id: UUID) -> bool:
    now = datetime.now(timezone.utc)
    result = session.exec(
        update(Job)
        .where(Job.id == job_id, Job.status == JobStatus.QUEUED)
        .values(status=JobStatus.RUNNING, updated_at=now)
        .execution_options(synchronize_session=False)
    )
    session.commit()
    return (result.rowcount or 0) == 1


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
    if _job_updates_deck_status(job):
        deck.status = DeckStatus.GENERATING
    deck.updated_at = now
    _append_log(workspace, f"{now.isoformat()} running {job.type}")
    write_job_manifest(workspace, deck, job)
    session.add(deck)
    session.add(job)
    session.commit()
    session.refresh(job)


def _run_build_pptx(
    session: Session,
    settings: Settings,
    deck: DeckSession,
    workspace: Path,
) -> None:
    outline_path = workspace / "input" / "outline.md"
    deck_ir_path = workspace / "ir" / "deck.json"
    pptx_path = workspace / "out" / "deck.pptx"

    _append_agent_log(workspace, "读取规划大纲，转换为 Deck IR。")
    _run_builder(settings, workspace, "outline", outline_path, deck_ir_path, "--title", deck.title)
    _append_agent_log(workspace, "Deck IR 已生成，开始渲染可编辑 PPTX。")
    _run_builder(settings, workspace, "build", deck_ir_path, pptx_path)
    _append_agent_log(workspace, "PPTX 生成完成，可以下载。")
    preview = build_preview_artifacts(settings, pptx_path, workspace)
    if preview.page_paths:
        _append_agent_log(workspace, "已生成首页封面预览。")

    _add_file_asset(session, deck, FileKind.DECK_IR, deck_ir_path, "application/json")
    _add_file_asset(
        session,
        deck,
        FileKind.PPTX,
        pptx_path,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    if preview.page_paths:
        _add_file_asset(session, deck, FileKind.PREVIEW, preview.page_paths[0], "image/png")
    elif preview.best_download() is not None:
        preview_path, preview_content_type = preview.best_download()
        _add_file_asset(session, deck, FileKind.PREVIEW, preview_path, preview_content_type)
    _add_file_asset(session, deck, FileKind.LOG, workspace / "logs" / "job.log", "text/plain")


def _run_plan_outline(
    session: Session,
    settings: Settings,
    deck: DeckSession,
    plan_job: Job,
    workspace: Path,
) -> bool:
    artifact = write_hermes_plan(settings, deck, workspace)
    planned_outline = artifact.outline_path.read_text(encoding="utf-8").strip()
    deck.outline_md = planned_outline + "\n"
    _add_file_asset(session, deck, FileKind.OUTLINE, artifact.outline_path, "text/markdown")
    _add_file_asset(session, deck, FileKind.LOG, workspace / "logs" / "job.log", "text/plain")
    if not settings.hermes_auto_build_after_plan:
        return False

    build_job = Job(
        deck_session_id=deck.id,
        owner_user_id=deck.owner_user_id,
        type=JobType.BUILD_PPTX,
        input_snapshot=deck.outline_md,
    )
    build_workspace = materialize_job_workspace(settings, deck, build_job)
    build_job.workspace_path = str(build_workspace)
    session.add(build_job)
    _append_agent_log(workspace, "已自动创建 PPTX 生成任务。")
    write_job_manifest(workspace, deck, plan_job)
    return True


def _run_hermes_review(
    session: Session,
    settings: Settings,
    deck: DeckSession,
    workspace: Path,
) -> None:
    artifact = write_hermes_review(settings, session, deck, workspace)
    _add_file_asset(session, deck, FileKind.REVIEW, artifact.report_path, "text/markdown")
    if artifact.preview_path is not None and artifact.preview_content_type is not None:
        _add_file_asset(session, deck, FileKind.PREVIEW, artifact.preview_path, artifact.preview_content_type)
    _add_file_asset(session, deck, FileKind.LOG, workspace / "logs" / "job.log", "text/plain")


def _job_updates_deck_status(job: Job) -> bool:
    return job.type in {JobType.BUILD_PPTX, JobType.PLAN_OUTLINE}


def _run_builder(
    settings: Settings,
    workspace: Path,
    subcommand: str,
    *args: Path | str,
) -> None:
    command = [*shlex.split(settings.builder_command), subcommand, *[str(arg) for arg in args]]
    env = os.environ.copy()
    if settings.template_pptx_path:
        env["AIPPT_TEMPLATE_PPTX"] = settings.template_pptx_path
    result = subprocess.run(
        command,
        cwd=workspace,
        env=env,
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


def _append_agent_log(workspace: Path, line: str) -> None:
    _append_log(workspace, f"AIPPT_AGENT: {line}")
