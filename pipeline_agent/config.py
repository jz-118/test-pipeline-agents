from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str = ""
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model: str = ""
    timeout_seconds: int = 120
    max_rounds: int = 3
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            api_key=os.getenv("VOLCENGINE_API_KEY", ""),
            base_url=os.getenv("VOLCENGINE_BASE_URL", cls.base_url).rstrip("/"),
            model=os.getenv("VOLCENGINE_MODEL", ""),
            timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "120")),
            max_rounds=max(1, int(os.getenv("AGENT_MAX_ROUNDS", "3"))),
            dry_run=os.getenv("AGENT_DRY_RUN", "false").lower() in {"1", "true", "yes"},
        )
