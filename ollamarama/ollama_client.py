from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests

from .exceptions import NetworkError, RuntimeFailure


class OllamaClient:
    """HTTP client for the Ollama Chat API.

    This client is synchronous; when used from async code, run calls in a thread
    executor (e.g., asyncio.to_thread) to avoid blocking the event loop.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/api",
        timeout: int = 180,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = int(timeout)
        self._session = session or requests.Session()

    # ---- Public API ----
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Send a non-streaming chat request and return parsed JSON.

        Raises NetworkError on HTTP/transport issues; RuntimeFailure on malformed responses.
        """
        url = f"{self.base_url}/chat"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if options is not None:
            payload["options"] = options
        # Some servers accept a 'timeout' field in the body; preserve compatibility
        if timeout is not None:
            payload["timeout"] = int(timeout)
        try:
            resp = self._session.post(url, json=payload, timeout=(self.timeout if timeout is None else int(timeout)))
            resp.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(str(e))

        try:
            data = resp.json()
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from Ollama: {e}")
        return data

    def health(self) -> bool:
        """Best-effort health check against the Ollama API.

        Tries a cheap endpoint (`/tags`). Not all servers may implement it; in
        that case, fall back to a HEAD on `/chat`.
        """
        tags = f"{self.base_url}/tags"
        try:
            r = self._session.get(tags, timeout=5)
            if r.ok:
                return True
        except requests.RequestException:
            pass
        # Fallback
        try:
            r = self._session.head(f"{self.base_url}/chat", timeout=5)
            return r.ok
        except requests.RequestException:
            return False

