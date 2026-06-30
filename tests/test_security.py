from types import SimpleNamespace

import pytest

from ollamarama.security import Security

try:
    from nio import KeyVerificationStart, KeyVerificationKey, KeyVerificationMac
except Exception:  # pragma: no cover - library missing
    KeyVerificationStart = KeyVerificationKey = KeyVerificationMac = object  # type: ignore


class FakeDevice:
    def __init__(self, device_id, verified=False):
        self.device_id = device_id
        self.verified = verified


class FakeDeviceStore:
    def __init__(self, by_user):
        self._by_user = by_user

    def active_user_devices(self, user_id):
        return iter(self._by_user.get(user_id, []))


class FakeClient:
    def __init__(self):
        self.verified = []
        self.device_store = FakeDeviceStore(
            {"@u": [FakeDevice("D1", False), FakeDevice("D2", True)]}
        )
        self.keys_queried = 0
        self.accepted = []
        self.confirmed = []
        self.sent = []
        self.key_verifications = {"t1": FakeSas()}
        self.device_id = "BOT"

    async def keys_query(self):
        self.keys_queried += 1
        return None

    def verify_device(self, device):
        self.verified.append(device.device_id)
        return True

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
    assert fake.client.keys_queried == 1
    assert fake.client.verified == ["D1"]


@pytest.mark.asyncio
async def test_security_allow_devices_supports_legacy_devices_mapping():
    fake = SimpleNamespace(client=FakeClient())
    fake.client.device_store = SimpleNamespace(
        devices={"@u": {"D1": FakeDevice("D1", False), "D2": FakeDevice("D2", True)}}
    )
    sec = Security(fake)
    await sec.allow_devices("@u")
    assert fake.client.verified == ["D1"]


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
    assert fake.client.sent

    key = KeyVerificationKey({}, "@u", "t1", "key")  # type: ignore[arg-type]
    await sec.emoji_verification_callback(key)
    assert fake.client.confirmed == ["t1"]

    mac = KeyVerificationMac({}, "@u", "t1", {}, "keys")  # type: ignore[arg-type]
    await sec.emoji_verification_callback(mac)
    assert fake.client.sent[-1].type == "m.key.verification.done"

