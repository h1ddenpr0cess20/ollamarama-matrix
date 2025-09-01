# Security Hardening Guide

This guide provides practical steps to deploy the bot more safely in real rooms. Review and adapt based on your homeserver, risk profile, and compliance needs.

## Bot Account & Devices

- Create a dedicated Matrix account for the bot; do not reuse personal accounts.
- Enable end‑to‑end encryption (E2EE) in rooms wherever possible.
- Verify the bot’s device keys with an admin account before allowing broad use.
- Periodically review the bot’s active devices and remove stale ones.

## Rooms, Permissions, and Scope

- Invite the bot only to rooms where it is needed; prefer private rooms for testing.
- Restrict who can use admin‑only commands (e.g., model changes) via room access controls and bot configuration.
- Consider read‑only rooms or rate limits for high‑traffic spaces.

## Prompts, Inputs, and Output Handling

- Treat all user inputs as untrusted. Avoid forwarding secrets to models.
- Be aware that responses may contain links or untrusted content. Use client‑side rendering that avoids executing scripts.
- If you export or mirror content outside Matrix, sanitize it and redact sensitive details.

## Configuration and Secrets

- Store configuration files outside of world‑readable paths; set restrictive permissions (e.g., `chmod 600 config.json`).
- Do not commit real API keys or credentials. Use templates or environment variables.
- Prefer least‑privilege keys/tokens where applicable; rotate credentials periodically.

## Logging and Data Retention

- Avoid logging full prompts or responses in production. Log only what is necessary for debugging (e.g., event IDs, error summaries).
- If logs must include content during debugging, ensure short retention, access controls, and redaction.
- Consider disabling or minimizing persistent history, or scoping it per‑room/user with clear retention expectations.

## Network and Runtime

- Run the bot under a dedicated OS user with minimal filesystem permissions.
- Place the bot behind a firewall; allow outbound connections only to required endpoints (homeserver, Ollama, etc.).
- Keep Python and dependencies up to date. Use `requirements.txt` pinning and scan for known CVEs.

## Dependency Hygiene

- Periodically update pinned dependencies after testing.
- Use `pip hash` or tools like `pip-tools` if you need stronger supply‑chain controls.
- Review transitive dependencies for licenses and security posture.

## Abuse, Misuse, and Rate Limiting

- Consider adding soft limits (e.g., per‑user rate limits, message length caps) to reduce abuse risk and cost.
- Monitor for prompt‑injection attempts and unexpected tool activation; constrain capabilities by default.

## Backups and Recovery

- Back up minimal configuration and state you cannot easily recreate (e.g., device IDs if needed). Exclude secrets from backups or encrypt them.
- Document the steps to re‑provision the bot account and re‑verify devices.

## Operational Practices

- Test changes in a non‑production room first.
- Use feature flags or configuration toggles for risky changes.
- Keep a changelog of model updates and configuration changes that affect behavior.

## Responsible Use

- Share the AI Output Disclaimer (`docs/ai-output-disclaimer.md`) with users. Set expectations about non‑professional use and risks.
- Follow applicable laws and organizational policies.

