import asyncio
from types import SimpleNamespace

import pytest

from ollamarama.security import Security


class FakeDevice:
    def __init__(self, verified=False):
        self.verified = verified


class FakeClient:
    def __init__(self):
        self.verified = []
        self.device_store = SimpleNamespace(devices={"@u": {"D1": FakeDevice(False), "D2": FakeDevice(True)}})

    async def query_keys(self, users):  # pragma: no cover - behavior not asserted
        return None

    async def verify_device(self, user_id, device_id):
        self.verified.append((user_id, device_id))


@pytest.mark.asyncio
async def test_security_allow_devices_verifies_unverified():
    fake = SimpleNamespace(client=FakeClient())
    sec = Security(fake)
    await sec.allow_devices("@u")
    # Should attempt to verify only unverified (D1)
    assert ("@u", "D1") in fake.client.verified

