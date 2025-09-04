from __future__ import annotations

from typing import Dict, List, Optional


class HistoryStore:
    """In-memory history per room and user with system prompt support."""

    def __init__(
        self,
        prompt_prefix: str,
        prompt_suffix: str,
        personality: str,
        *,
        prompt_suffix_extra: str = "",
        max_items: int = 24,
    ) -> None:
        self.prompt_prefix = prompt_prefix
        self.prompt_suffix = prompt_suffix
        # Optional extra suffix (e.g., brevity clause). Included unless verbose mode is enabled.
        self.prompt_suffix_extra = prompt_suffix_extra
        self._include_extra = True
        self.personality = personality
        self.max_items = max_items
        self._messages: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

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

    def clear_all(self) -> None:
        """Remove all rooms and histories."""
        self._messages.clear()

    def _trim(self, room: str, user: str) -> None:
        """Trim oldest messages to maintain the configured maximum length."""
        msgs = self._messages[room][user]
        while len(msgs) > self.max_items:
            if msgs and msgs[0].get("role") == "system":
                # Preserve system if present
                if len(msgs) > 1:
                    msgs.pop(1)
                else:
                    break
            else:
                msgs.pop(0)
