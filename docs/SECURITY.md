# JARVIS Security Architecture & Policy Guardrails

Security is a primary requirement in JARVIS. Autonomous agents must never execute unconstrained destructive actions.

---

## 1. Authentication & Device Authorization
- **JWT Cryptographic Bearer Tokens**: All API endpoints and client WebSockets require valid signed JWT access tokens (`HS256`).
- **Cryptographic Device Hashing**: Device nodes (Phone, Laptop) authenticate using a high-entropy device secret (`jarvis_dev_...`). Secrets are never stored in plaintext in the database; only SHA-256 hashes (`api_token_hash`) are persisted.
- **Revocable Node Access**: Any compromised device can be immediately revoked via `DELETE /api/v1/auth/devices/{device_id}`.

---

## 2. Dangerous Command Guardrails
The `DecisionEngine` intercepts all requested tool calls. Destructive commands are blocked and require explicit user confirmation:

### Destructive Patterns Blocked:
- Recursive root deletion: `rm -rf /` or `rm -rf ~`
- Filesystem formatting: `mkfs`, `format C:`, `del /f /s /q C:\`
- Raw block device overwrites: `dd if=...`, `> /dev/sd*`
- Database drops: `DROP DATABASE ...`
- System power overrides: `shutdown`, `reboot`

---

## 3. Secret Sanitization & Least Privilege
- **Automatic Secret Masking (`sanitize_secrets`)**: All tool arguments, outputs, stdout/stderr streams, and logs are scanned with regular expressions matching API key signatures (`sk-...`, `ghp_...`, Bearer tokens). Any detected keys are replaced with `***REDACTED_SECRET***` before being returned to the UI or stored in the database.
- **Sandboxed Workspaces**: File system tools enforce workspace boundaries (`settings.WORKSPACE_ROOT`), preventing traversal outside designated project roots.
- **Audit Logging**: Every command execution is logged in the `AuditLog` table with timestamp, caller device ID, command string (sanitized), and execution status.
