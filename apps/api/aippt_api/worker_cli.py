import argparse
from uuid import UUID

from sqlmodel import Session

from .config import get_settings
from .db import create_db_and_tables, get_engine
from .services.job_runner import run_job, run_next_job


def main() -> None:
    parser = argparse.ArgumentParser(prog="aippt-worker")
    sub = parser.add_subparsers(dest="command", required=True)

    run_once = sub.add_parser("run-once")
    run_once.add_argument("--job-id", default=None)

    args = parser.parse_args()
    settings = get_settings()
    create_db_and_tables()

    with Session(get_engine()) as session:
        if args.command == "run-once" and args.job_id:
            job = run_job(session, settings, UUID(args.job_id))
        else:
            job = run_next_job(session, settings)

    if job is None:
        print("no queued jobs")
        return
    print(f"{job.id} {job.status}")


if __name__ == "__main__":
    main()
