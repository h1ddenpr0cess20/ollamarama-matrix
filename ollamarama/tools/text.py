from __future__ import annotations

import re
from typing import Dict, Any

def text_stats(text: str) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        return {"words": 0, "characters": 0, "sentences": 0}
    words = re.findall(r"\b\w+\b", text)
    sentences = re.findall(r"[.!?]+", text)
    return {
        "words": len(words),
        "characters": len(text),
        "sentences": len(sentences),
    }
