from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from .agents import ContextAgent, ExecutorAgent, ReviewAgent
from .config import Settings
from .provider import ChatProvider
from .workspace import TestWorkspace, WorkspaceViolation


class Orchestrator:
    def __init__(self, root: Path, settings: Settings):
        provider = ChatProvider(settings.api_key, settings.base_url, settings.model, settings.timeout_seconds)
        workspace = TestWorkspace(root)
        self.settings, self.workspace = settings, workspace
        self.context, self.executor, self.reviewer = ContextAgent(provider), ExecutorAgent(provider, workspace), ReviewAgent(provider)

    def run(self, request: str, base_ref: str | None = None, head_ref: str | None = None) -> dict:
        started = time.monotonic()
        diff = self._commit_diff(base_ref, head_ref)
        if self.settings.dry_run:
            return {"status": "dry-run", "files": self.workspace.list_tests(), "diff": diff}
        context = self.context.summarize(self.workspace.list_tests(), diff)
        history: list[dict] = []
        for round_no in range(1, self.settings.max_rounds + 1):
            self._check_timeout(started)
            summary = self.executor.apply(request, context, self.workspace.git_diff())
            self._check_allowed_diff()
            test_result = self._run_tests()
            review = self.reviewer.review(self.workspace.git_diff(), test_result)
            history.append({"round": round_no, "summary": summary, "test_result": test_result, "review": review})
            if review.get("approved") and "failed" not in test_result.lower():
                return {"status": "approved", "rounds": history}
            request = f"Fix only these test-layer issues: {review.get('issues', [])}. Original request: {request}"
        return {"status": "needs-human-review", "rounds": history}

    def _run_tests(self) -> str:
        result = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=self.workspace.root, text=True, capture_output=True, timeout=self.settings.timeout_seconds)
        return (result.stdout + "\n" + result.stderr)[-12000:]

    def _commit_diff(self, base_ref: str | None, head_ref: str | None) -> str:
        if not base_ref or not head_ref:
            return self.workspace.git_diff()
        result = subprocess.run(["git", "diff", f"{base_ref}...{head_ref}", "--", str(self.workspace.root)], cwd=self.workspace.root, text=True, capture_output=True)
        return result.stdout[-30000:]

    def _check_allowed_diff(self) -> None:
        result = subprocess.run(["git", "status", "--short"], cwd=self.workspace.root, text=True, capture_output=True)
        violations = []
        for line in result.stdout.splitlines():
            relative = line[3:].strip() if len(line) >= 4 else ""
            if relative and not relative.replace("\\", "/").startswith("tests/"):
                violations.append(relative)
        if violations:
            raise WorkspaceViolation(f"forbidden changed files: {violations}")

    def _check_timeout(self, started: float) -> None:
        if time.monotonic() - started > self.settings.timeout_seconds:
            raise TimeoutError("agent task exceeded total timeout")
