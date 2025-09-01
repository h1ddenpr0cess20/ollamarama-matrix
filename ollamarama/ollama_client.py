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
        """Send a chat request and return the parsed JSON response.

        Args:
            messages: Conversation messages in ChatML-like format.
            model: Model name or ID to use.
            options: Optional model-specific parameters.
            timeout: Optional request timeout override in seconds.
            stream: Whether to request a streaming response (kept for API compatibility).

        Returns:
            Parsed JSON response from the Ollama server.

        Raises:
            NetworkError: If the HTTP request fails or the server returns an error.
            RuntimeFailure: If the response body is not valid JSON.
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

        Tries `/tags` first, falling back to a `HEAD` on `/chat` if needed.

        Returns:
            True if a quick request succeeds; otherwise False.
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

    def list_models(self) -> Dict[str, str]:
        """Return a mapping of available model names from the server.

        Uses the `/tags` endpoint, which typically returns a payload like
        `{"models": [{"name": "qwen3"}, ...]}`.

        Returns:
            Mapping of model name to model identifier (usually the same string).

        Raises:
            NetworkError: If the HTTP request fails.
            RuntimeFailure: If the response is invalid or contains no models.
        """
        url = f"{self.base_url}/tags"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise NetworkError(str(e))
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from Ollama: {e}")

        models: Dict[str, str] = {}
        try:
            items = data.get("models", []) if isinstance(data, dict) else []
            for item in items:
                name = None
                if isinstance(item, dict):
                    name = item.get("name") or item.get("model")
                if isinstance(name, str) and name:
                    models[name] = name
        except Exception:
            pass
        if not models:
            raise RuntimeFailure("No models found in Ollama /tags response")
        return models
