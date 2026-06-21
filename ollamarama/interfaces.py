from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, Awaitable, Callable


class OllamaClientProtocol(Protocol):
    """Structural interface for an Ollama chat client."""

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        options: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Send a chat request and return the parsed response."""
        ...

    def health(self) -> bool:
        """Return True if the Ollama server is reachable."""
        ...


class MatrixClientProtocol(Protocol):
    """Structural interface for the Matrix client wrapper."""

    async def login(self) -> Any:
        """Log in to the homeserver."""
        ...

    async def ensure_keys(self) -> None:
        """Upload encryption keys if needed."""
        ...

    async def load_store(self) -> None:
        """Load the local encryption store if available."""
        ...

    async def join(self, room_id: str) -> None:
        """Join a room by ID or alias."""
        ...

    async def leave(self, room_id: str) -> None:
        """Leave (or reject an invite to) a room."""
        ...

    async def request_room_key(self, event: Any) -> None:
        """Request the Megolm session key for an undecryptable event."""
        ...

    async def send_text(self, room_id: str, body: str, html: Optional[str] = None) -> None:
        """Send a text message to a room."""
        ...

    async def display_name(self, user_id: str) -> str:
        """Return a user's display name, falling back to the user ID."""
        ...

    def add_text_handler(self, handler: Callable[[Any, Any], Awaitable[None]]) -> None:
        """Register a callback for text message events."""
        ...

    def add_event_handler(self, handler: Callable[[Any, Any], Awaitable[None]], event_type: Any) -> None:
        """Register a callback for an arbitrary room event type."""
        ...

    def add_invite_handler(self, handler: Callable[[Any, Any], Awaitable[None]]) -> None:
        """Register a callback for room invite events."""
        ...

    def add_megolm_handler(self, handler: Callable[[Any, Any], Awaitable[None]]) -> None:
        """Register a callback for undecryptable encrypted events."""
        ...

    def add_to_device_callback(self, callback, event_types=None) -> None:
        """Register a to-device event callback."""
        ...

    async def initial_sync(self, timeout_ms: int = 3000) -> None:
        """Perform an initial sync to populate local state."""
        ...

    async def sync_forever(self, timeout_ms: int = 30000) -> None:
        """Run the Matrix sync loop indefinitely."""
        ...


class HistoryStoreProtocol(Protocol):
    """Structural interface for the conversation history store."""

    def init_prompt(self, room: str, user: str, persona: Optional[str] = None, custom: Optional[str] = None) -> None:
        """Initialize or replace the system prompt for a room/user."""
        ...

    def add(self, room: str, user: str, role: str, content: str) -> None:
        """Append a message to a room/user conversation."""
        ...

    def get(self, room: str, user: str) -> List[Dict[str, str]]:
        """Return the message list for a room/user."""
        ...

    def reset(self, room: str, user: str, stock: bool = False) -> None:
        """Clear history for a room/user."""
        ...

    def clear_all(self) -> None:
        """Remove all rooms and histories."""
        ...
