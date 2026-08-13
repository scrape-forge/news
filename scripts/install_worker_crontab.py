#!/usr/bin/env python3
"""Install idempotent cron entries for registered news workers."""

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from news.workers.cli import WORKERS  # noqa: E402


MARKER_PREFIX = "news-worker"
RETIRED_WORKERS = frozenset({"tags"})


def invokes_worker(line: str, workers: set[str] | frozenset[str]) -> bool:
    """Return whether an unmarked cron line invokes one of the workers."""
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#"):
        return False
    return any(
        re.search(
            rf"(?<!\S)-m\s+news\.workers\s+{re.escape(worker)}(?=\s|$)",
            line,
        )
        for worker in workers
    )


def parse_schedule_overrides(values: list[str]) -> dict[str, str]:
    overrides = {}
    for value in values:
        worker, separator, schedule = value.partition("=")
        if (
            not separator
            or worker not in WORKERS
            or not schedule.strip()
            or "\n" in schedule
            or "\r" in schedule
        ):
            available = ", ".join(WORKERS)
            raise ValueError(
                f"invalid schedule '{value}'; use WORKER=CRON "
                f"(available workers: {available})"
            )
        if len(schedule.split()) != 5:
            raise ValueError(
                f"schedule for '{worker}' must contain exactly five cron fields"
            )
        overrides[worker] = schedule.strip()
    return overrides


def selected_workers(positional_workers: list[str]) -> list[str]:
    if positional_workers:
        workers = list(dict.fromkeys(positional_workers))
    else:
        configured = os.getenv("CRON_WORKERS", "enrich")
        workers = [item.strip() for item in configured.split(",") if item.strip()]
    unknown = [worker for worker in workers if worker not in WORKERS]
    if unknown:
        raise ValueError(f"unknown worker(s): {', '.join(unknown)}")
    return list(dict.fromkeys(workers))


def environment_schedule_overrides(workers: list[str]) -> list[str]:
    values = []
    for worker in workers:
        suffix = worker.upper().replace("-", "_")
        schedule = os.getenv(f"WORKER_CRON_{suffix}")
        if schedule:
            values.append(f"{worker}={schedule}")
    return values


def remove_managed_blocks(crontab: str, workers: set[str]) -> str:
    output = []
    skipped_worker = None
    for line in crontab.splitlines():
        if line.startswith(f"# BEGIN {MARKER_PREFIX}:"):
            candidate = line.partition(":")[2].strip()
            if candidate in workers or candidate not in WORKERS:
                skipped_worker = candidate
                continue
        if skipped_worker is not None:
            if line == f"# END {MARKER_PREFIX}:{skipped_worker}":
                skipped_worker = None
            continue
        # Older images installed worker commands without management markers.
        # Replace selected workers and remove explicitly retired commands while
        # preserving all unrelated cron jobs.
        if invokes_worker(line, workers | RETIRED_WORKERS):
            continue
        output.append(line)
    return "\n".join(output).strip()


def render_worker_block(
    worker: str,
    schedule: str,
    *,
    project_dir: Path,
    python_bin: Path,
    log_dir: Path,
) -> str:
    command = " ".join(
        [
            "cd",
            shlex.quote(str(project_dir)),
            "&&",
            shlex.quote(str(python_bin)),
            "-u -m news.workers",
            shlex.quote(worker),
            ">>",
            shlex.quote(str(log_dir / f"{worker}.log")),
            "2>&1",
        ]
    )
    return "\n".join(
        [
            f"# BEGIN {MARKER_PREFIX}:{worker}",
            f"{schedule} {command}",
            f"# END {MARKER_PREFIX}:{worker}",
        ]
    )


def build_crontab(
    current: str,
    workers: list[str],
    schedules: dict[str, str],
    *,
    project_dir: Path,
    python_bin: Path,
    log_dir: Path,
    remove: bool,
) -> str:
    updated = remove_managed_blocks(current, set(workers))
    if not remove:
        blocks = [
            render_worker_block(
                worker,
                schedules.get(worker, WORKERS[worker].default_cron),
                project_dir=project_dir,
                python_bin=python_bin,
                log_dir=log_dir,
            )
            for worker in workers
        ]
        updated = "\n\n".join(part for part in [updated, *blocks] if part)
    return f"{updated}\n" if updated else ""


def read_crontab(crontab_file: Path | None) -> str:
    if crontab_file is not None:
        return crontab_file.read_text(encoding="utf-8") if crontab_file.exists() else ""

    result = subprocess.run(
        ["crontab", "-l"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "could not read crontab")
    return result.stdout if result.returncode == 0 else ""


def write_crontab(crontab: str, crontab_file: Path | None) -> None:
    if crontab_file is not None:
        crontab_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=crontab_file.parent,
            prefix=f".{crontab_file.name}.",
            delete=False,
        ) as temporary_file:
            temporary_file.write(crontab)
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, crontab_file)
        return

    subprocess.run(
        ["crontab", "-"],
        input=crontab,
        text=True,
        check=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install cron entries for registered news workers."
    )
    parser.add_argument(
        "workers",
        nargs="*",
        help="Workers to manage (default: CRON_WORKERS or enrich).",
    )
    parser.add_argument(
        "--schedule",
        action="append",
        default=[],
        metavar="WORKER=CRON",
        help='Override a schedule, e.g. --schedule "enrich=*/5 * * * *".',
    )
    parser.add_argument("--project-dir", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--python",
        dest="python_bin",
        type=Path,
        default=Path(sys.executable),
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(os.getenv("WORKER_LOG_DIR", PROJECT_ROOT / "logs/workers")),
    )
    parser.add_argument(
        "--crontab-file",
        type=Path,
        help="Write a cron file directly instead of the current user's crontab.",
    )
    parser.add_argument("--remove", action="store_true", help="Remove selected workers.")
    parser.add_argument("--dry-run", action="store_true", help="Print without installing.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        workers = selected_workers(args.workers)
        schedules = parse_schedule_overrides(
            [*environment_schedule_overrides(workers), *args.schedule]
        )
        if not workers:
            raise ValueError("no workers selected")
        current = read_crontab(args.crontab_file)
        updated = build_crontab(
            current,
            workers,
            schedules,
            project_dir=args.project_dir.resolve(),
            python_bin=args.python_bin.absolute(),
            log_dir=args.log_dir.resolve(),
            remove=args.remove,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    if args.dry_run:
        print(updated, end="")
        return 0

    if not args.remove:
        args.log_dir.mkdir(parents=True, exist_ok=True)
    write_crontab(updated, args.crontab_file)
    action = "Removed" if args.remove else "Installed"
    print(f"{action} cron entries for: {', '.join(workers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
