# Integrations

## Local connectors

- **Identity:** Keycloak OIDC with PKCE, self-registration, email verification, required TOTP action and recovery. Mailpit captures local messages at port 8025.
- **Odoo:** official Odoo 19 Community container, isolated database per Nexora workspace and a signed ORM addon. Implemented commands include CRM/contact/product create/update, quotations, purchase orders/receipts and draft invoices/bills/posting.
- **Control plane:** PostgreSQL, Alembic schema versioning, tenant-scoped membership, audit and idempotency.

The attendance endpoint accepts signed, timestamped device events after a workspace owner/admin/HR manager creates a device credential; no vendor-specific attendance adapter is connected yet. A separate `ATTENDANCE_DEVICE_MASTER_KEY` encrypts issued credentials at rest. Payment gateways/events are not connected. Finance can record a manual payment and match its exact amount against a posted invoice as an audited control-plane alternative; it does not create an Odoo `account.payment` or reconcile journal items. WhatsApp, couriers, external stores, background queues and production mail are not connected.

Documents accept private `.txt` uploads up to 2 MiB on a persistent local Compose volume. The API verifies UTF-8 text, hashes content, writes tenant-isolated files with restrictive permissions and audits authenticated downloads. Rich formats, antivirus scanning, external object storage and customer-facing sharing are not configured. Back up the `nexora-documents` volume with the database so uploaded content stays paired with its metadata.

Create/rotate a workspace key with `POST /api/v1/hr/attendance/device-credentials`; the raw key is returned once. Device events are sent to `POST /api/v1/hr/attendance/device-events` with `X-Tenant-ID`, `X-Device-Key-ID`, `X-Device-Timestamp` and `X-Device-Signature`. The signature is lowercase hex HMAC-SHA256 over `<timestamp>.<tenant-uuid>.<raw-request-body>`. The body includes the same tenant ID, provider event ID, employee number, ISO timestamp and `check_in` or `check_out`. Duplicate provider event IDs are ignored within the tenant. Revoking the credential immediately blocks further events.

For each provider, document supported actions/events, required scopes, sandbox vs production behavior, secret storage/rotation, request signing, retries/idempotency, rate limits, health state, error review and disconnect behavior. Keep credentials server-side and encrypted. Show a secret only at issuance when applicable. Event history must preserve request IDs and safe redacted errors. Odoo calls include a timestamp, request ID and HMAC; idempotency receipts and ORM changes share the Odoo transaction.

## Local API clients

Workspace owners/admins can create API clients from the Automation & insights menu. Choose a non-privileged role, one branch and an expiry from 1 to 365 days. The random `nxo_live_` bearer token is displayed once; PostgreSQL stores only its SHA-256 digest. Requests include both `Authorization: Bearer <token>` and that workspace's `X-Tenant-ID`. Tokens are bound to the issuing member and branch, and role, branch or membership changes revoke that member's existing API tokens. Use the client list's status control to revoke one token. These local tokens are for trusted server-side integrations; they do not enable external webhook delivery, rate limiting or production monitoring.

Example request after creating a client:

```sh
curl http://localhost:8000/api/v1/records/leads \
  -H 'Authorization: Bearer nxo_live_REPLACE_WITH_THE_ONE_TIME_TOKEN' \
  -H 'X-Tenant-ID: REPLACE_WITH_WORKSPACE_UUID'
```

Commerce and operations resources use `/api/v1/workspace/{kind}` in the local control plane and PostgreSQL RLS. Workflow actions are deliberately restricted to safe state updates or approval requests. The workspace assistant uses permission-scoped deterministic search and reports when it has no matching source; it does not send data to an external model. POS sales/close and budget spend are tenant-audited local ledgers and are not posted into Odoo cash/accounting journals. CSV/JSON export and integration health records do not imply an external connector or background delivery service.
