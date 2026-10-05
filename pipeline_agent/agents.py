from __future__ import annotations

import json
from dataclasses import dataclass

from .provider import ChatProvider
from .workspace import TestWorkspace


CONTEXT_PROMPT = """You maintain a compact factual summary of a repository's test layer. Never propose production-code changes. Return concise JSON with test_framework, test_roots, conventions, and risks."""
EXECUTOR_PROMPT = """You modify tests only. You may return a JSON object {\"files\":[{\"path\":\"tests/...\",\"content\":\"...\"}],\"summary\":\"...\"}. Every path must be under tests/. Never modify production code, CI files, dependencies, or secrets. Do not include markdown fences."""
REVIEW_PROMPT = """You are a stateless, read-only test reviewer. Review only the supplied test diff and result. Return JSON {\"approved\":true/false,\"issues\":[...],\"reason\":\"...\"}. Do not write files and do not suggest production-code edits."""


@dataclass
class ContextAgent:
    provider: ChatProvider

    def summarize(self, files: list[str], diff: str) -> str:
        return self.provider.complete(CONTEXT_PROMPT, json.dumps({"files": files, "diff": diff})[:30000])


@dataclass
class ExecutorAgent:
    provider: ChatProvider
    workspace: TestWorkspace

    def apply(self, request: str, context: str, diff: str) -> str:
        raw = self.provider.complete(EXECUTOR_PROMPT, json.dumps({"request": request, "context": context, "diff": diff})[:50000])
        try:
            patch = json.loads(raw)
            for item in patch.get("files", []):
                self.workspace.write(item["path"], item["content"])
            return patch.get("summary", "tests updated")
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"executor returned invalid JSON: {exc}") from exc


@dataclass
class ReviewAgent:
    provider: ChatProvider

    def review(self, diff: str, test_result: str) -> dict:
        raw = self.provider.complete(REVIEW_PROMPT, json.dumps({"diff": diff, "test_result": test_result})[:50000])
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"reviewer returned invalid JSON: {exc}") from exc
