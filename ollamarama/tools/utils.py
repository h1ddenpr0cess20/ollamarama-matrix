from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any


def get_time(timezone_name: str = "UTC") -> Dict[str, Any]:
    tz = (timezone_name or "UTC").strip()
    if tz.upper() == "UTC":
        return {"datetime": datetime.now(timezone.utc).isoformat(), "timezone": "UTC"}
    if tz.lower() == "local":
        return {"datetime": datetime.now().isoformat(), "timezone": "local"}
    # Try ZoneInfo if available (Python 3.9+), else fallback
    try:
        from zoneinfo import ZoneInfo  # type: ignore

        return {"datetime": datetime.now(ZoneInfo(tz)).isoformat(), "timezone": tz}
    except Exception:
        return {"error": f"Unsupported timezone '{tz}'. Use 'UTC' or 'local'."}
