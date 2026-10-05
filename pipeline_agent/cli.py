from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Settings
from .orchestrator import Orchestrator


def main() -> int:
    parser = argparse.ArgumentParser(prog="pipeline-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="generate/review tests for a commit")
    run.add_argument("request", nargs="?", default="Analyze the current commit and add missing regression tests.")
    run.add_argument("--root", type=Path, default=Path.cwd())
    run.add_argument("--base-ref")
    run.add_argument("--head-ref")
    run.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    settings = Settings.from_env()
    if getattr(args, "dry_run", False):
        settings = settings.__class__(**{**settings.__dict__, "dry_run": True})
    try:
        result = Orchestrator(args.root.resolve(), settings).run(args.request, args.base_ref, args.head_ref)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"approved", "dry-run", "needs-human-review"} else 1
