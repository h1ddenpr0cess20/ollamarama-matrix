import asyncio
from types import SimpleNamespace

import pytest

from ollamarama.security import Security

try:
    from nio import KeyVerificationStart, KeyVerificationKey, KeyVerificationMac
except Exception:  # pragma: no cover - library missing
    KeyVerificationStart = KeyVerificationKey = KeyVerificationMac = object  # type: ignore


class FakeDevice:
    def __init__(self, verified=False):
        self.verified = verified


class FakeClient:
    def __init__(self):
        self.verified = []
        self.device_store = SimpleNamespace(devices={"@u": {"D1": FakeDevice(False), "D2": FakeDevice(True)}})
        self.accepted = []
        self.confirmed = []
        self.sent = []
        self.key_verifications = {"t1": FakeSas()}
        self.device_id = "BOT"

    async def query_keys(self, users):  # pragma: no cover - behavior not asserted
        return None

    async def verify_device(self, user_id, device_id):
        self.verified.append((user_id, device_id))

    async def accept_key_verification(self, txn_id):
        self.accepted.append(txn_id)

    async def confirm_short_auth_string(self, txn_id):
        self.confirmed.append(txn_id)

    async def to_device(self, msg):
        self.sent.append(msg)


class FakeSas:
    def __init__(self):
        self.other_olm_device = SimpleNamespace(id="DEV1")

    def share_key(self):
        return SimpleNamespace(type="m.key.verification.key", recipient="@u", recipient_device="DEV1", content={})

    def get_emoji(self):
        return ["😀"]


@pytest.mark.asyncio
async def test_security_allow_devices_verifies_unverified():
    fake = SimpleNamespace(client=FakeClient())
    sec = Security(fake)
    await sec.allow_devices("@u")
    # Should attempt to verify only unverified (D1)
    assert ("@u", "D1") in fake.client.verified


@pytest.mark.asyncio
async def test_log_to_device_event_sends_ready():
    fake = SimpleNamespace(client=FakeClient())
    sec = Security(fake)
    event = SimpleNamespace(
        type="m.key.verification.request",
        source={"content": {"transaction_id": "t1", "from_device": "DEVX"}},
        sender="@u",
    )
    await sec.log_to_device_event(event)
    assert fake.client.sent and fake.client.sent[0].type == "m.key.verification.ready"


@pytest.mark.asyncio
async def test_emoji_verification_callback_flow():
    fake = SimpleNamespace(client=FakeClient())
    sec = Security(fake)

    start = KeyVerificationStart({}, "@u", "t1", "DEVX", "m.sas.v1", [], [], [], ["emoji"])  # type: ignore[arg-type]
    await sec.emoji_verification_callback(start)
    assert fake.client.accepted == ["t1"]
    assert fake.client.sent  # share_key message sent

    key = KeyVerificationKey({}, "@u", "t1", "key")  # type: ignore[arg-type]
    await sec.emoji_verification_callback(key)
    assert fake.client.confirmed == ["t1"]

    mac = KeyVerificationMac({}, "@u", "t1", {}, "keys")  # type: ignore[arg-type]
    await sec.emoji_verification_callback(mac)
    assert fake.client.sent[-1].type == "m.key.verification.done"

