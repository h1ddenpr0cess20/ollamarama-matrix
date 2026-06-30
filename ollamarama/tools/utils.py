from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any


def get_time(timezone_name: str = "UTC") -> Dict[str, Any]:
    """Return the current time for a timezone in ISO 8601 format.

    Args:
        timezone_name: ``"UTC"``, ``"local"``, or an IANA timezone name
            (e.g., ``"America/New_York"``). Defaults to ``"UTC"``.

    Returns:
        ``{"datetime": iso_string, "timezone": name}`` on success, or
        ``{"error": str}`` for an unsupported timezone.
    """
    tz = (timezone_name or "UTC").strip()
    if tz.upper() == "UTC":
        return {"datetime": datetime.now(timezone.utc).isoformat(), "timezone": "UTC"}
    if tz.lower() == "local":
        return {"datetime": datetime.now().isoformat(), "timezone": "local"}
    try:
        from zoneinfo import ZoneInfo  # type: ignore

        return {"datetime": datetime.now(ZoneInfo(tz)).isoformat(), "timezone": tz}
    except Exception:
        return {"error": f"Unsupported timezone '{tz}'. Use 'UTC' or 'local'."}
