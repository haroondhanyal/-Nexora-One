# Five-phase implementation checklist

Use this as the shared delivery checklist. A menu, button or card does not complete a feature. Completion requires working behavior, persistence, authorization and appropriate verification. Keep the app runnable after each phase.

**Current delivery:** The local stack connects Next.js to Keycloak OIDC, a FastAPI/PostgreSQL control plane and per-tenant Odoo 19 databases through a signed ORM addon. Phases 4–5 include a tenant-RLS resource store and connected screens for local commerce/operations records, manual workflows, auditable budget and POS cash ledgers, imports, JSON/CSV exports, reports, custom fields and deterministic source-scoped record search. Payroll supports effective-dated monthly components with calendar-day proration for mid-period hires and salary changes; statutory and attendance-based rules are not applied. Phase 2 includes a manual exact-amount payment matching alternative. These alternatives provide local operational tracking; they do not replace external processors, public portals, Odoo accounting postings or an AI provider. Checkboxes stay open until behavior, persistence, authorization and verification evidence is complete. No phase has met its full exit criteria.

**Known Phase 1 gaps:** workspace chooser/redirect validation, platform administration/support access, Odoo profile synchronization, production identity/session revocation, and cross-tenant/branch/disabled-user security verification. Company address/currency/timezone, tenant-scoped theme preferences, and invitation resend endpoints now persist through the control plane; delivery behavior still needs runtime verification.

**Known Phase 2 gaps:** payment provider event intake and Odoo payment posting/reconciliation (manual exact-amount matching is an audited local alternative); stock reservations/transfers and branch-to-warehouse mapping (single default-location physical counts are wired but need Odoo runtime verification); full-stock sales delivery is implemented but needs runtime verification alongside confirmed-order invoicing and receipt-to-draft-vendor-bill flows; budget spend ledger calculations are implemented locally but need API/database runtime verification; and verification of all Odoo postings.

**Known Phase 3 gaps:** no named attendance-device vendor adapter (the signed generic event endpoint needs a vendor adapter and runtime secret); no attendance-based proration, statutory tax, benefit, accrual or jurisdiction-specific payroll rules; approved payroll CSV export is implemented, but no payroll payment execution; no verified timekeeping/payroll journeys or salary-access security checks. Generic calendar-day proration is covered by isolated calculation checks but still needs end-to-end DB/API and salary-privacy verification.

**Known Phase 4 gaps:** current storefront/order, POS, returns, project, ticket and field-job records are local operational metadata with guarded status flows. Public storefront/catalog/cart/checkout, payment capture/refunds, Odoo stock-backed delivery/returns, POS-to-Odoo cash posting, rich file uploads, customer/supplier portals, maintenance contracts and end-to-end responsive journey evidence are not connected. Private plain-text documents up to 2 MiB can be stored locally; external object storage and malware scanning are absent.

**Known Phase 5 gaps:** automation is manually started and limited to status changes or approval requests; no scheduler/worker exists. Saved operational reports now group authorized workspace records by status or branch with an optional status filter; there is no report designer for arbitrary fields/formulas or scheduled delivery. Imports accept bounded JSON rows; exports are scoped JSON/CSV without field mapping. Local record search is deterministic and does not call an AI model. API clients now issue one-time, hashed, expiring bearer tokens scoped to a branch and restricted role; external signed webhook delivery/history, industry packs, distributed tracing, deployment and demonstrated backup restore remain incomplete. Token auth and report API still need runtime security verification.

## Phase 1 — Foundation, authentication and administration

- [ ] Repository conventions, pinned dependencies, local environment and architecture decisions
- [ ] OIDC login, owner signup, email verification, recovery, MFA, session rotation/revocation and generic credential errors
- [ ] Portal context selector that does not grant roles; authorized membership chooser and role-aware redirect
- [ ] Recoverable tenant provisioning, owner onboarding and platform administration
- [ ] Company profile, branches, invitations, users, roles, permissions and last-owner safeguards
- [ ] Profiles, preferences, five themes, accessible responsive staff shell and audit events
- [ ] Odoo connection registry, capability checks and gateway foundation
- [ ] Security checks for cross-tenant, branch, disabled user and revoked-role cases

**Exit:** signup, invitation, authorized redirect, reset, sign-out revocation and theme preference work; tenant boundaries and role changes are enforced by the backend; local startup instructions are verified.

## Phase 2 — Core ERP and financial operations

- [ ] CRM leads and customer records
- [ ] Quotations, sales orders, delivery and invoicing
- [ ] Suppliers, purchase orders, receipts and supplier bills
- [ ] Products, stock, reservations, transfers and adjustments
- [ ] Payments, provider events, idempotency and reconciliation
- [ ] Budgets, reports and operational approvals

**Exit:** lead-to-order-to-invoice and purchase-to-receipt-to-bill journeys reconcile with authoritative Odoo data. Duplicate requests do not duplicate postings; posted documents are protected.

## Phase 3 — HR, attendance and payroll

- [ ] Employees, departments and effective-dated employment records
- [ ] Shifts, attendance capture, correction review and leave
- [ ] Supported attendance-device adapter
- [ ] Salary structures and payroll preparation/approval
- [ ] Released payslips, advances and payroll reporting
- [ ] Employee self-service and salary-field restrictions

**Exit:** attendance through approval, payroll and payslip is reproducible and auditable. Verified calculations and own-record access are covered.

## Phase 4 — Commerce, POS, services and portals

- [ ] Store builder, storefront theme, domain, catalog and cart/checkout
- [ ] Payment status, fulfillment, returns, refunds and promotions
- [ ] POS sessions, sales, close and cash reconciliation
- [ ] Projects, timesheets, service tickets, field jobs and maintenance contracts
- [ ] Documents, approvals and customer/supplier/employee portal isolation
- [ ] Responsive primary journeys and service completion evidence

**Exit:** order/payment/delivery/return, concurrent stock rules, POS close, portal isolation and service evidence work.

## Phase 5 — AI, automation and production readiness

- [ ] Permission-scoped AI sources, transparent unavailable answers and approval-bound actions
- [ ] Workflow designer, run history, idempotent retries and safe actions
- [ ] Analytics, report designer, scheduled reports and scoped exports
- [ ] API clients, hashed tokens, signed webhooks and delivery history
- [ ] Custom fields and functioning industry packs
- [ ] Integration health, import/export and recovery workflows
- [ ] Performance, structured logs, request IDs, tracing, CI/CD and operations runbooks
- [ ] Backup restore demonstration and accurate release documentation

**Exit:** authorized AI, approval for consequential actions, safe retries, no cross-tenant/salary leakage, functioning industry workflows, demonstrated restore and passing release checks.
