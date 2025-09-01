from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

try:
    from nio import AsyncClient, AsyncClientConfig, MatrixRoom, RoomMessageText
except Exception:  # pragma: no cover - allow import in environments without nio
    AsyncClient = object  # type: ignore
    AsyncClientConfig = object  # type: ignore
    MatrixRoom = object  # type: ignore
    RoomMessageText = object  # type: ignore


TextHandler = Callable[[Any, Any], Awaitable[None]]


class MatrixClientWrapper:
    """Thin wrapper around nio.AsyncClient for easier testing and composition.

    Provides a cleaner surface for handlers and isolates Matrix I/O.
    """

    def __init__(
        self,
        server: str,
        username: str,
        password: str,
        device_id: str = "",
        store_path: str = "store",
        encryption_enabled: bool = True,
    ) -> None:
        cfg = AsyncClientConfig(encryption_enabled=encryption_enabled, store_sync_tokens=True)
        self.client = AsyncClient(server, username, device_id=device_id or None, store_path=store_path, config=cfg)
        # Set user_id for convenience (matches original behavior)
        try:
            self.client.user_id = username  # type: ignore[attr-defined]
        except Exception:
            pass
        self.password = password

    async def login(self) -> Any:
        return await self.client.login(self.password, device_name=self.client.device_id or "ollamarama")

    async def ensure_keys(self) -> None:
        if getattr(self.client, "should_upload_keys", False):
            await self.client.keys_upload()

    async def load_store(self) -> None:
        """Load local store if available (encryption state)."""
        result = getattr(self.client, "load_store", None)
        if callable(result):
            maybe = result()
            if asyncio.iscoroutine(maybe):
                await maybe

    async def join(self, room_id: str) -> None:
        await self.client.join(room_id)

    async def send_text(self, room_id: str, body: str, html: Optional[str] = None) -> None:
        content = {"msgtype": "m.text", "body": body}
        if html is not None:
            content.update({"format": "org.matrix.custom.html", "formatted_body": html})
        await self.client.room_send(room_id=room_id, message_type="m.room.message", content=content, ignore_unverified_devices=True)

    async def display_name(self, user_id: str) -> str:
        try:
            res = await self.client.get_displayname(user_id)
            return getattr(res, "displayname", user_id)
        except Exception:
            return user_id

    def add_text_handler(self, handler: TextHandler) -> None:
        async def _cb(room: MatrixRoom, event: RoomMessageText) -> None:  # type: ignore
            await handler(room, event)

        self.client.add_event_callback(_cb, RoomMessageText)  # type: ignore

    def add_to_device_callback(self, callback, event_types=None) -> None:
        try:
            self.client.add_to_device_callback(callback, event_types)
        except Exception:
            # nio not available or crypto not initialized
            pass

    async def initial_sync(self, timeout_ms: int = 3000) -> None:
        await self.client.sync(timeout=timeout_ms, full_state=True)

    async def sync_forever(self, timeout_ms: int = 30000) -> None:
        await self.client.sync_forever(timeout=timeout_ms, full_state=True)
