from __future__ import annotations

import re
from typing import Dict, Any

def text_stats(text: str) -> Dict[str, Any]:
    """Return word, character, and sentence counts for a string.

    Args:
        text: The text to analyze.

    Returns:
        A mapping with ``words``, ``characters``, and ``sentences`` counts.
        Returns zero counts for empty or non-string input.
    """
    if not isinstance(text, str) or not text.strip():
        return {"words": 0, "characters": 0, "sentences": 0}
    words = re.findall(r"\b\w+\b", text)
    sentences = re.findall(r"[.!?]+", text)
    return {
        "words": len(words),
        "characters": len(text),
        "sentences": len(sentences),
    }
