from __future__ import annotations

from typing import Tuple

__all__ = ["split_thinking"]


def split_thinking(text: str) -> Tuple[str, str]:
    """Separate chain-of-thought markers from visible response content.

    Handles the three marker styles emitted by reasoning models:
    ``<think>…</think>``, ``<|begin_of_thought|>…<|end_of_thought|>``, and
    ``<|begin_of_solution|>…<|end_of_solution|>``. Malformed or partial markers
    are left untouched. ``None`` is treated as an empty string.

    Args:
        text: The raw model response content.

    Returns:
        A ``(visible, thinking)`` tuple where ``visible`` is the stripped,
        user-facing text and ``thinking`` is the extracted reasoning (joined
        by newlines, empty if none was found).
    """
    text = text or ""
    thinking_parts = []

    if "<think>" in text and "</think>" in text:
        try:
            thinking, rest = text.split("</think>", 1)
            thinking_parts.append(thinking.replace("<think>", "").strip())
            text = rest
        except Exception:
            # Malformed reasoning markers just mean the text is left as-is.
            pass

    if "<|begin_of_thought|>" in text and "<|end_of_thought|>" in text:
        try:
            parts = text.split("<|end_of_thought|>")
            if len(parts) > 1:
                thinking_parts.append(
                    parts[0].replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                )
                text = parts[1]
        except Exception:
            # Malformed reasoning markers just mean the text is left as-is.
            pass

    if "<|begin_of_solution|>" in text and "<|end_of_solution|>" in text:
        try:
            text = text.split("<|begin_of_solution|>", 1)[1].split("<|end_of_solution|>", 1)[0]
        except Exception:
            # Malformed solution markers just mean the text is left as-is.
            pass

    return text.strip(), "\n".join(t for t in thinking_parts if t)
