"""Command-line entry point for background workers."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

from news.workers import enrich_articles


@dataclass(frozen=True)
class WorkerSpec:
    name: str
    help: str
    handler: Callable[[argparse.Namespace], int]
    default_cron: str


def _run_enrich(args: argparse.Namespace) -> int:
    return enrich_articles.run(
        batch_size=args.batch_size,
        max_requests=args.max_requests,
    )


WORKERS = {
    "enrich": WorkerSpec(
        name="enrich",
        help="Generate structured Papagon Insight article enrichment.",
        handler=_run_enrich,
        default_cron="*/1 * * * *",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m news.workers",
        description="Run a news background worker.",
    )
    subparsers = parser.add_subparsers(dest="worker", required=True)

    enrich_spec = WORKERS["enrich"]
    enrich_parser = subparsers.add_parser(enrich_spec.name, help=enrich_spec.help)
    enrich_parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Articles sent in each request (default: BATCH_SIZE or 5).",
    )
    enrich_parser.add_argument(
        "--max-requests",
        type=int,
        default=None,
        help="Maximum requests for this run (default: MAX_RPM or 12).",
    )
    enrich_parser.set_defaults(handler=enrich_spec.handler)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
