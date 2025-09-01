from __future__ import annotations

import logging
from typing import Any, Optional

try:  # best-effort imports; code degrades gracefully if nio not present
    from nio import KeyVerificationEvent
except Exception:  # pragma: no cover
    KeyVerificationEvent = object  # type: ignore


class Security:
    """E2E helpers: logs to-device events and attempts basic device allowance.

    This is a pragmatic reconstruction of the prior verification mixin: it logs
    verification events and attempts to mark devices as verified to avoid
    blocked messages. For full interactive SAS verification, a dedicated flow
    can be added later.
    """

    def __init__(self, matrix_client, logger: Optional[logging.Logger] = None) -> None:
        self.matrix = matrix_client
        self.logger = logger or logging.getLogger(__name__)

    def log_to_device_event(self, client: Any, event: Any) -> None:  # callback signature per nio
        try:
            etype = type(event).__name__
        except Exception:
            etype = "<unknown>"
        self.logger.info("to-device event: %s", etype)

    def emoji_verification_callback(self, client: Any, event: Any) -> None:  # KeyVerificationEvent
        etype = type(event).__name__
        self.logger.info("verification event: %s", etype)

    async def allow_devices(self, user_id: str) -> None:
        """Trust devices for the given user to prevent send failures.

        Strategy:
        - Query devices (if API available).
        - Mark unverified devices as verified (best-effort) to avoid blocking.
        """
        c = getattr(self.matrix, "client", None)
        if c is None:
            return
        try:
            # Query device list to populate store, if available
            if hasattr(c, "query_keys"):
                await c.query_keys([user_id])  # type: ignore
        except Exception:
            pass
        try:
            store = getattr(c, "device_store", None)
            devices = {}
            if store is not None:
                devices = getattr(store, "devices", {}).get(user_id, {})
            for device_id, dev in dict(devices).items():
                # dev.verified may exist; if not, attempt verify anyway
                try:
                    if getattr(dev, "verified", False):
                        continue
                    if hasattr(c, "verify_device"):
                        await c.verify_device(user_id, device_id)  # type: ignore
                        self.logger.info("verified device %s for %s", device_id, user_id)
                except Exception:
                    # Ignore failures; sending uses ignore_unverified_devices=True
                    pass
        except Exception:
            pass
