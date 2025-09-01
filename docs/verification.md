# Device Verification (Matrix E2EE)

This page explains how device verification works for the bot, why it matters, how to verify the bot from another device, and proposed improvements to make the process clearer and safer.

## What “verification” means

- Matrix end‑to‑end encryption (E2EE) uses per‑device keys. Devices must be verified (trusted) so encrypted messages can be decrypted reliably without warnings or failures.
- Verifying the bot’s device with your admin (or operator) device establishes trust and reduces encryption errors in E2EE rooms.

## What the bot does today

- Auto‑handles verification requests: when a `m.key.verification.request` arrives, the bot replies with “ready” for the `m.sas.v1` (emoji) method.
- Auto‑accepts and completes SAS (emoji) flows: upon `start` and `key` events, the bot accepts, shares its key, logs the emojis to the console, confirms the short auth string, and sends MAC/done to conclude.
- Best‑effort device allowance: before responding to a user, the bot queries device lists and attempts to mark unverified sender devices as verified to avoid blocked sends.
- Sends while ignoring unverified devices: outbound messages set `ignore_unverified_devices=True` to reduce failures in partially verified rooms.

Notes:

- The bot logs the verification emojis it sees, but it does not require a human to confirm them. On most clients, you start the verification from your side and see it complete successfully.
- Device state (Olm/Megolm keys, trust) is persisted in the `store/` directory and tied to the `device_id`. The app writes the `device_id` back to your config after first login when possible.

## Why you should still verify the bot

- Verifying the bot’s device from a trusted admin device ensures both sides trust each other’s keys in E2EE rooms.
- Without verification, some clients warn or may refuse to decrypt; room history and replies can be flaky during initial key exchange.

## How to verify the bot (Element/compatible clients)

1. Start a DM with the bot account (or open its member profile in a shared room).
2. Choose “Verify” or “Verify device.”
3. Pick the emoji (SAS) method.
4. The bot automatically accepts and completes the flow; you should see the verification succeed on your client.
5. Optional: verify the bot from multiple admin devices if several operators will manage it.

Tips:

- If you rotate the bot’s device (new `device_id`, fresh `store/`), repeat the verification.
- Keep `store/` safe and persistent between runs to avoid re‑verification surprises.

## Configuration and persistence

- `matrix.e2e` (config): enable/disable encryption. When disabled, verification is not used.
- `matrix.store_path` (config): where encryption state is stored (default: `store/`). Back it up cautiously; it contains sensitive keys.
- `matrix.device_id` (config): optional. If omitted, it is written back after first login. Changing it creates a new device from Matrix’s perspective.

## Troubleshooting

- No verification prompt appears:
  - Ensure E2EE is enabled in the room and your homeserver supports it.
  - Confirm `matrix-nio[e2e]` and `libolm` are installed on the bot host.
  - Check logs for to‑device traffic and verification messages.
- Replies fail or are missing in E2EE rooms:
  - Verify the bot’s device from your admin device.
  - Confirm the bot is in the room and has synced after joining.
  - Persist `store/` so device and session keys aren’t lost between runs.
- After reinstall/migration:
  - If the bot shows up as a new device, re‑verify it. You may remove trust for old/stale devices in your client.

## Current limitations

- Auto‑confirmation: the bot confirms SAS without human comparison of emojis. This is convenient but less strict than a manual check.
- Broad allowance: the bot attempts to mark sender devices as verified to reduce failures, which can be overly permissive in some threat models.

## Proposed improvements

- Verification policy toggles:
  - `auto_accept_requests`: accept incoming verification requests automatically (default: true).
  - `auto_confirm_sas`: auto‑confirm emoji SAS, or require an admin approval step (default: true → can be set to false).
  - `auto_verify_devices`: mark sender devices as verified automatically (default: false in stricter mode).
- Admin‑gated approvals:
  - Post the emoji list in a designated admin room or DM and require an explicit `.verify <txid>` command before confirming.
  - Time out pending verifications if not approved within N minutes.
- Scope restrictions:
  - Only accept verification from configured `matrix.admins` or from users in the same room.
  - Optionally restrict to a homeserver allowlist.
- Operator tooling:
  - Commands to list known devices for a user (`.devices @user`), verify a specific device, and revoke/forget trust.
  - Command to show the bot’s current `device_id` and verification status.
- UX and logging:
  - Clearer log messages and optional audit file for verification events.
  - Health endpoint or CLI status that surfaces E2EE readiness.
- Alternative methods:
  - Add QR code verification when supported by the client library.

If you’d like these tightened defaults or admin‑approval flows, open an issue describing your use case and desired policy. We can add config flags and a small command surface to fit stricter environments without breaking convenience for simple setups.

