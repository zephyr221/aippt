import argparse
import time
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
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
    loop = sub.add_parser("loop")
    loop.add_argument("--sleep-seconds", type=float, default=5.0)
    loop.add_argument("--concurrency", type=int, default=None)

    args = parser.parse_args()
    settings = get_settings()
    create_db_and_tables()

    if args.command == "loop":
        concurrency = max(1, args.concurrency or settings.worker_concurrency)
        if concurrency == 1:
            _loop_forever(settings, args.sleep_seconds, "worker-1")
            return

        with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="aippt-worker") as executor:
            futures = [
                executor.submit(_loop_forever, settings, args.sleep_seconds, f"worker-{idx}")
                for idx in range(1, concurrency + 1)
            ]
            wait(futures, return_when=FIRST_EXCEPTION)
            for future in futures:
                future.result()
        return

    with Session(get_engine()) as session:
        if args.job_id:
            job = run_job(session, settings, UUID(args.job_id))
        else:
            job = run_next_job(session, settings)

    if job is None:
        print("no queued jobs")
        return
    print(f"{job.id} {job.status}")


def _loop_forever(settings, sleep_seconds: float, worker_name: str) -> None:
    while True:
        with Session(get_engine()) as session:
            job = run_next_job(session, settings)
        if job is not None:
            print(f"{worker_name} {job.id} {job.status}", flush=True)
            continue
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
