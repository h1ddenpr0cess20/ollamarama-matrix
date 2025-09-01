from __future__ import annotations

import logging
from typing import Any, Optional

try:  # best-effort imports; code degrades gracefully if nio not present
    from nio import (
        KeyVerificationEvent,
        KeyVerificationStart,
        KeyVerificationKey,
        KeyVerificationMac,
        KeyVerificationCancel,
        ToDeviceMessage,
    )
except Exception:  # pragma: no cover
    KeyVerificationEvent = object  # type: ignore
    KeyVerificationStart = object  # type: ignore
    KeyVerificationKey = object  # type: ignore
    KeyVerificationMac = object  # type: ignore
    KeyVerificationCancel = object  # type: ignore
    ToDeviceMessage = object  # type: ignore


class Security:
    """E2E helpers for device verification and allowance.

    Provides basic SAS emoji verification handling and attempts to mark devices
    as verified to avoid blocked messages. This mirrors the legacy
    VerificationMixin behaviour but in a separate helper class.
    """

    def __init__(self, matrix_client, logger: Optional[logging.Logger] = None) -> None:
        self.matrix = matrix_client
        self.logger = logger or logging.getLogger(__name__)

    async def log_to_device_event(self, event: Any) -> None:
        """Log to-device events and respond to verification requests.

        Args:
            event: An incoming to-device event object from the Matrix client.

        Returns:
            None.
        """
        try:
            etype = type(event).__name__
        except Exception:
            etype = "<unknown>"
        raw_type = getattr(event, "type", None)
        if raw_type and raw_type != etype:
            self.logger.info("to-device event: %s (%s)", etype, raw_type)
        else:
            self.logger.info("to-device event: %s", etype)

        # Respond to verification requests so the emoji flow can proceed
        if getattr(event, "type", None) == "m.key.verification.request":
            try:
                txn_id = event.source["content"]["transaction_id"]  # type: ignore[index]
                from_device = event.source["content"]["from_device"]  # type: ignore[index]
                client = getattr(self.matrix, "client", None)
                if client is None:
                    return
                content = {
                    "from_device": getattr(client, "device_id", ""),
                    "methods": ["m.sas.v1"],
                    "transaction_id": txn_id,
                }
                msg = ToDeviceMessage(
                    "m.key.verification.ready",
                    event.sender,  # type: ignore[attr-defined]
                    from_device,
                    content,
                )
                await client.to_device(msg)  # type: ignore[attr-defined]
                self.logger.info("Verification ready message sent.")
            except Exception:
                self.logger.info("Failed to send verification ready message.")

    async def emoji_verification_callback(self, event: Any) -> None:  # KeyVerificationEvent
        """Handle SAS emoji verification events.

        Args:
            event: A verification-related event carrying state for the flow.

        Returns:
            None.
        """
        client = getattr(self.matrix, "client", None)
        if client is None:
            return
        try:
            if isinstance(event, KeyVerificationStart):
                if "emoji" not in getattr(event, "short_authentication_string", []):
                    return
                await client.accept_key_verification(event.transaction_id)  # type: ignore[attr-defined]
                sas = client.key_verifications[event.transaction_id]
                await client.to_device(sas.share_key())
            elif isinstance(event, KeyVerificationKey):
                sas = client.key_verifications[event.transaction_id]
                emojis = sas.get_emoji()
                self.logger.info("Emoji verification requested: %s", emojis)
                await client.confirm_short_auth_string(event.transaction_id)
            elif isinstance(event, KeyVerificationMac):
                sas = client.key_verifications[event.transaction_id]
                # Prefer sending our MAC (more correct SAS completion) when available.
                try:
                    if hasattr(sas, "get_mac"):
                        await client.to_device(sas.get_mac())
                    elif hasattr(sas, "send_mac"):
                        await client.to_device(sas.send_mac())
                    elif hasattr(client, "send_sas_mac"):
                        await client.send_sas_mac(event.transaction_id)  # type: ignore[attr-defined]
                except Exception:
                    # Fallback to just sending done if MAC helpers are unavailable
                    pass

                # Always send `done` to conclude the flow; harmless if already sent.
                try:
                    done = ToDeviceMessage(
                        "m.key.verification.done",
                        event.sender,  # type: ignore[attr-defined]
                        sas.other_olm_device.id,
                        {"transaction_id": event.transaction_id},
                    )
                    await client.to_device(done)
                except Exception:
                    pass
                self.logger.info("Emoji verification was successful.")
            elif isinstance(event, KeyVerificationCancel):
                self.logger.info("Verification cancelled.")
        except Exception:
            self.logger.info("Exception during emoji verification.")

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
