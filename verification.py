# Verification and authentication utilities for ollamarama
from nio import (
    KeyVerificationEvent,
    KeyVerificationStart,
    KeyVerificationKey,
    KeyVerificationMac,
    KeyVerificationCancel,
    ToDeviceMessage,
)

class VerificationMixin:
    async def allow_devices(self, user_id):
        """Ensure messages can be sent to all of a user's devices."""
        try:
            for device in self.client.device_store.active_user_devices(user_id):
                try:
                    if self.client.olm.is_device_blacklisted(device):
                        self.client.unblacklist_device(device)
                    if not self.client.olm.is_device_verified(device):
                        self.client.ignore_device(device)
                except Exception as e:
                    self.log(f"Failed to allow device {device.id} for {user_id}: {e}")
        except Exception as e:
            self.log(f"Failed to allow devices for {user_id}: {e}")

    async def emoji_verification_callback(self, event):
        """Auto-accept incoming emoji verification requests (SAS)."""
        client = self.client
        try:
            if isinstance(event, KeyVerificationStart):
                if "emoji" not in event.short_authentication_string:
                    return
                await client.accept_key_verification(event.transaction_id)
                sas = client.key_verifications[event.transaction_id]
                todevice_msg = sas.share_key()
                await client.to_device(todevice_msg)
            elif isinstance(event, KeyVerificationKey):
                sas = client.key_verifications[event.transaction_id]
                emojis = sas.get_emoji()
                self.log(f"Emoji verification requested: {emojis}")
                await client.confirm_short_auth_string(event.transaction_id)
            elif isinstance(event, KeyVerificationMac):
                sas = client.key_verifications[event.transaction_id]
                try:
                    done = ToDeviceMessage(
                        "m.key.verification.done",
                        event.sender,
                        sas.other_olm_device.id,
                        {"transaction_id": event.transaction_id},
                    )
                    await client.to_device(done)
                    self.log("Emoji verification was successful.")
                except Exception:
                    self.log("Failed to complete emoji verification.")
            elif isinstance(event, KeyVerificationCancel):
                self.log("Verification cancelled.")
        except Exception:
            self.log("Exception during emoji verification.")

    async def log_to_device_event(self, event):
        """Handle to-device events for SAS verification."""
        if hasattr(event, 'type') and event.type == "m.key.verification.request":
            try:
                txn_id = event.source['content']['transaction_id']
                from_device = event.source['content']['from_device']
                self.log("Verification ready message sent.")
                content = {
                    "from_device": self.device_id,
                    "methods": ["m.sas.v1"],
                    "transaction_id": txn_id
                }
                message = ToDeviceMessage(
                    "m.key.verification.ready",
                    event.sender,
                    from_device,
                    content,
                )
                await self.client.to_device(message)
            except Exception:
                self.log("Failed to send verification ready message.")
