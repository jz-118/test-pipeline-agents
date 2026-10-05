from __future__ import annotations

import subprocess
from pathlib import Path


class WorkspaceViolation(RuntimeError):
    pass


class TestWorkspace:
    """Filesystem boundary: agents may only write under the configured test root."""

    def __init__(self, root: Path, test_dir: str = "tests"):
        self.root = root.resolve()
        self.test_root = (self.root / test_dir).resolve()
        if not self.test_root.is_relative_to(self.root):
            raise WorkspaceViolation("test directory escapes repository root")

    def read(self, relative: str) -> str:
        path = self._path(relative)
        return path.read_text(encoding="utf-8")

    def write(self, relative: str, content: str) -> None:
        path = self._path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_tests(self) -> list[str]:
        if not self.test_root.exists():
            return []
        return sorted(str(p.relative_to(self.root)) for p in self.test_root.rglob("*") if p.is_file())

    def git_diff(self) -> str:
        result = subprocess.run(["git", "diff", "--", str(self.test_root)], cwd=self.root, text=True, capture_output=True)
        chunks = [result.stdout]
        # `git diff` omits untracked test files; include their contents for review.
        status = subprocess.run(["git", "status", "--short", "--", str(self.test_root)], cwd=self.root, text=True, capture_output=True)
        for line in status.stdout.splitlines():
            relative = line[3:].strip() if len(line) >= 4 else ""
            if line.startswith("??") and relative:
                path = (self.root / relative).resolve()
                if path.is_file() and path.is_relative_to(self.test_root):
                    chunks.append(f"\n--- untracked {relative} ---\n{path.read_text(encoding='utf-8')}\n")
        return "".join(chunks)

    def _path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if not candidate.is_relative_to(self.test_root) or candidate == self.test_root:
            raise WorkspaceViolation(f"only files under {self.test_root} may be changed")
        return candidate
