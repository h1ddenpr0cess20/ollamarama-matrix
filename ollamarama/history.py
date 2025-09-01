from __future__ import annotations

from typing import Dict, List, Optional


class HistoryStore:
    """In-memory history per room and user with system prompt support."""

    def __init__(self, prompt_prefix: str, prompt_suffix: str, personality: str, max_items: int = 24) -> None:
        self.prompt_prefix = prompt_prefix
        self.prompt_suffix = prompt_suffix
        self.personality = personality
        self.max_items = max_items
        self._messages: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

    def _ensure(self, room: str, user: str) -> None:
        if room not in self._messages:
            self._messages[room] = {}
        if user not in self._messages[room]:
            self._messages[room][user] = [
                {"role": "system", "content": f"{self.prompt_prefix}{self.personality}{self.prompt_suffix}"}
            ]

    def init_prompt(self, room: str, user: str, persona: Optional[str] = None, custom: Optional[str] = None) -> None:
        self._ensure(room, user)
        if custom:
            self._messages[room][user] = [{"role": "system", "content": custom}]
        else:
            p = persona if (persona is not None and persona != "") else self.personality
            self._messages[room][user] = [
                {"role": "system", "content": f"{self.prompt_prefix}{p}{self.prompt_suffix}"}
            ]

    def add(self, room: str, user: str, role: str, content: str) -> None:
        self._ensure(room, user)
        self._messages[room][user].append({"role": role, "content": content})
        self._trim(room, user)

    def get(self, room: str, user: str) -> List[Dict[str, str]]:
        self._ensure(room, user)
        return list(self._messages[room][user])

    def reset(self, room: str, user: str, stock: bool = False) -> None:
        if room not in self._messages:
            self._messages[room] = {}
        self._messages[room][user] = []
        if not stock:
            self.init_prompt(room, user, persona=self.personality)

    def clear_all(self) -> None:
        self._messages.clear()

    def _trim(self, room: str, user: str) -> None:
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

