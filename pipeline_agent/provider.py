from __future__ import annotations

import json
import urllib.error
import urllib.request


class ProviderError(RuntimeError):
    pass


class ChatProvider:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 120):
        self.api_key, self.base_url, self.model, self.timeout = api_key, base_url, model, timeout

    def complete(self, system: str, user: str) -> str:
        if not self.api_key or not self.model:
            raise ProviderError("VOLCENGINE_API_KEY and VOLCENGINE_MODEL must be set")
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.1,
        }).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ProviderError(str(exc)) from exc
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected provider response: {data}") from exc
