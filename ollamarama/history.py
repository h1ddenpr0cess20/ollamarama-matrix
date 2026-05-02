from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class HistoryStore:
    """In-memory history per room and user with system prompt support.

    When ``store_path`` and ``encryption_key`` are provided, history is
    persisted to an encrypted file and restored on startup.
    """

    def __init__(
        self,
        prompt_prefix: str,
        prompt_suffix: str,
        personality: str,
        *,
        prompt_suffix_extra: str = "",
        max_tokens: int = 8192,
        store_path: Optional[str] = None,
        encryption_key: Optional[str] = None,
    ) -> None:
        self.prompt_prefix = prompt_prefix
        self.prompt_suffix = prompt_suffix
        # Optional extra suffix (e.g., brevity clause). Included unless verbose mode is enabled.
        self.prompt_suffix_extra = prompt_suffix_extra
        self._include_extra = True
        self.personality = personality
        self.max_tokens = max_tokens
        self._messages: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

        # Encrypted persistence
        self._store_file: Optional[Path] = None
        self._fernet: Optional[Fernet] = None
        if store_path and encryption_key:
            self._store_file = Path(store_path) / "history.enc"
            self._store_file.parent.mkdir(parents=True, exist_ok=True)
            self._fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
            self._load()

    def set_verbose(self, verbose: bool) -> None:
        """Control whether to include the optional extra suffix for new conversations.

        Args:
            verbose: When True, omit the extra suffix (be more verbose).
        """
        self._include_extra = not bool(verbose)

    def _full_suffix(self) -> str:
        return f"{self.prompt_suffix}{self.prompt_suffix_extra if self._include_extra and self.prompt_suffix_extra else ''}"

    def _ensure(self, room: str, user: str) -> None:
        """Ensure internal structures exist for a room/user and seed system prompt."""
        if room not in self._messages:
            self._messages[room] = {}
        if user not in self._messages[room]:
            self._messages[room][user] = [
                {"role": "system", "content": f"{self.prompt_prefix}{self.personality}{self._full_suffix()}"}
            ]

    def init_prompt(self, room: str, user: str, persona: Optional[str] = None, custom: Optional[str] = None) -> None:
        """Initialize or replace the system prompt for a room/user.

        Args:
            room: Matrix room identifier.
            user: Matrix user identifier.
            persona: Optional persona appended to prefix/suffix.
            custom: Optional custom system prompt that replaces prefix/suffix.
        """
        self._ensure(room, user)
        if custom:
            self._messages[room][user] = [{"role": "system", "content": custom}]
        else:
            p = persona if (persona is not None and persona != "") else self.personality
            self._messages[room][user] = [
                {"role": "system", "content": f"{self.prompt_prefix}{p}{self._full_suffix()}"}
            ]
        self._save()

    def add(self, room: str, user: str, role: str, content: str) -> None:
        """Append a message to the conversation and trim history.

        Args:
            room: Matrix room identifier.
            user: Matrix user identifier.
            role: Role for the message (e.g., `user`, `assistant`, `system`).
            content: Message content.
        """
        self._ensure(room, user)
        self._messages[room][user].append({"role": role, "content": content})
        self._trim(room, user)
        self._save()

    def get(self, room: str, user: str) -> List[Dict[str, str]]:
        """Return a copy of the message list for a room/user."""
        self._ensure(room, user)
        return list(self._messages[room][user])

    def reset(self, room: str, user: str, stock: bool = False) -> None:
        """Clear history for a room/user, optionally leaving it empty.

        Args:
            room: Matrix room identifier.
            user: Matrix user identifier.
            stock: If True, do not re-seed with the configured system prompt.
        """
        if room not in self._messages:
            self._messages[room] = {}
        self._messages[room][user] = []
        if not stock:
            self.init_prompt(room, user, persona=self.personality)
        self._save()

    def clear_all(self) -> None:
        """Remove all rooms and histories."""
        self._messages.clear()
        self._save()

    @staticmethod
    def count_tokens(msgs: List[Dict[str, str]]) -> int:
        """Estimate token count for a list of messages using char-length heuristic."""
        return sum(len(m.get("content", "")) for m in msgs) // 4

    def _trim(self, room: str, user: str) -> None:
        """Trim oldest messages until estimated token count is within the configured limit."""
        msgs = self._messages[room][user]
        while self.count_tokens(msgs) > self.max_tokens:
            if msgs and msgs[0].get("role") == "system":
                # Preserve system prompt
                if len(msgs) > 1:
                    msgs.pop(1)
                else:
                    break
            else:
                msgs.pop(0)

    # -- Encrypted persistence -------------------------------------------------

    def _save(self) -> None:
        """Encrypt and write history to disk. No-op if persistence is not configured."""
        if not self._fernet or not self._store_file:
            return
        try:
            data = json.dumps(self._messages, separators=(",", ":")).encode()
            self._store_file.write_bytes(self._fernet.encrypt(data))
        except Exception:
            logger.exception("Failed to save encrypted history")

    def _load(self) -> None:
        """Decrypt and restore history from disk. No-op if file does not exist."""
        if not self._fernet or not self._store_file or not self._store_file.exists():
            return
        try:
            encrypted = self._store_file.read_bytes()
            data = self._fernet.decrypt(encrypted)
            self._messages = json.loads(data)
        except InvalidToken:
            logger.error(
                "Failed to decrypt history file — wrong key or corrupted data. "
                "Starting with empty history."
            )
        except Exception:
            logger.exception("Failed to load encrypted history")
