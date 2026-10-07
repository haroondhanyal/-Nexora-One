<p align="center">
  <img src="apps/web/public/brand/nexora-one-logo.svg" alt="Nexora One" width="360" />
</p>

<h1 align="center">Nexora One</h1>
<p align="center">One business operating platform for ERP, finance, people and commerce.</p>

> **Project status:** This repository includes a working local demo UI, illustrative sample records and a development API profile. Phases 1–5 remain in progress; none has passed its full exit criteria. The repo includes a Next.js client, FastAPI control plane, PostgreSQL migrations and row-level policies, Keycloak OIDC realm, Mailpit, per-tenant Odoo 19 Community databases and a signed transactional addon. Payroll supports effective-dated calendar-day proration for hires and compensation changes within a month. Phase 4–5 includes tenant-scoped operational resources, POS cash and budget ledgers, manual workflows, imports, JSON/CSV exports, analytics and local record search. Statutory payroll, provider checkout, authoritative fulfillment, external webhook/API delivery and production verification remain incomplete.

## Product overview

Nexora One is planned as a multi-tenant business platform for companies with multiple branches and industry-specific workflows. The product has separate experiences for platform administrators, company owners, staff, employees, customers, suppliers and public shoppers. Shared modules cover CRM, sales, finance, inventory, purchasing, HR, payroll, commerce, POS, projects, services, documents, approvals, reporting, automation and AI assistance.

The system is designed around a control plane for tenant, membership and configuration data, with a separate Odoo database per tenant for authoritative ERP records. Next.js is the web application, FastAPI is the tenant-aware API and orchestration layer, and Odoo owns ERP and financial business workflows. See [Architecture](docs/architecture.md) before implementing integrations.

## Architecture at a glance

Nexora One is currently a modular monolith: one web application and one API process, with PostgreSQL for control-plane and operational data. Odoo is an optional per-tenant ERP service in the Compose profile. The local VS Code profile uses a development identity and leaves Odoo and Keycloak offline.

```mermaid
flowchart LR
    U[Workspace users] --> W[Next.js web app]
    W -->|API proxy| A[FastAPI modular monolith]
    W -. OIDC in Compose profile .-> K[Keycloak]
    A --> P[(PostgreSQL control plane)]
    A -. signed ORM operations .-> O[Odoo tenant database]
    A --> F[(Private local text files)]
    K -. local mail .-> M[Mailpit]
```

| Layer | Repository location | Responsibility |
|---|---|---|
| Web and demo data | `apps/web/app/` | Workspace UI, screen registry, client-side API orchestration, reusable components and illustrative local records |
| API and domain modules | `services/api/app/` | Authentication, tenant and role checks, business APIs, HR/payroll and local operational workflows |
| Database history | `services/api/migrations/` | SQLAlchemy models and versioned PostgreSQL migrations with tenant row policies |
| ERP adapter | `services/api/app/odoo.py`, `odoo/addons/nexora_gateway/` | Tenant database provisioning and signed Odoo ORM commands |
| Identity UI/configuration | `identity/` | Local Keycloak realm and Nexora sign-in theme |
| Local developer operations | `.vscode/`, `compose.yaml`, `.github/workflows/` | VS Code no-Docker tasks, optional Compose services and continuous integration |

The current code boundaries, data ownership, tenant security rules and remaining architecture work are documented in [the architecture guide](docs/architecture.md).

## Current implementation status

| Area | Status |
|---|---|
| Brand logo, dark logo and favicon | Implemented as original SVG assets |
| Responsive Phase 1–3 workspace UI | Connected to API for implemented administration, ERP, HR, attendance and limited payroll workflows |
| Login, signup, verification, MFA and recovery | Keycloak OIDC realm/client configured for local development |
| API, database and migrations | FastAPI, PostgreSQL and Alembic baseline implemented |
| Tenant isolation and authorization | Membership, role, branch and PostgreSQL RLS checks implemented; security verification remains |
| Odoo gateway and business transactions | Per-tenant DB provisioner and signed ORM addon implemented; only supported commands are wired |
| HR, attendance and payroll foundations | Tenant-scoped APIs and role-limited self-service/review flows; payroll rules remain limited |
| Commerce and operations foundation | Tenant-scoped local storefront, orders, returns, POS session, projects, timesheets, service/field-job records, and private audited plain-text uploads with guarded transitions |
| Automation and insight foundation | Manual workflow runs and approvals, import/export, custom fields, live operational counts and permission-scoped local record search |
| Advanced application structure | Screen registry, shared workspace/domain utilities, focused overview/settings/table components and standalone payroll calculation module |
| Phases and screen ownership | Documented in `docs/` |

Menus and sample rows are not evidence that a backend capability is complete. Track behavior and exit criteria in [the phase checklist](docs/phases.md).

## Main capabilities

| Product area | Planned capabilities |
|---|---|
| Platform administration | Tenant provisioning, plans, health, support access and audit |
| Company administration | Workspace setup, branches, users, roles, permissions and settings |
| ERP and finance | CRM, sales, purchasing, inventory, invoices, payments and reports |
| People | Employees, attendance, leave, payroll and self-service |
| Commerce and operations | Online stores, POS, projects, service jobs and portals |
| Shared services | Documents, approvals, workflows, integrations, analytics and scoped AI |

## User roles

Platform administrators manage the SaaS control plane. Company owners and administrators configure a tenant. Managers and staff operate assigned departments and branches. Employees and technicians use self-service and field workflows. Customers and suppliers use restricted portals. Store visitors can browse and place public orders. A selected portal on the login screen is only context; the server must determine actual roles after authentication.

## Authentication and authorization

The web client uses OIDC Authorization Code with PKCE through the local Keycloak realm. Tokens stay in memory. The API verifies JWT signature, issuer and audience, then resolves active memberships on each request. Business records and branch assignments are checked server-side; PostgreSQL RLS protects tenant-keyed control-plane tables. Review [permissions](docs/permissions.md) and the remaining checks in [the phase checklist](docs/phases.md). This local realm is not a production configuration.

## Screens

The screens in Phases 1 through 5 connect to the local API where endpoints exist. Provider and production-only flows remain explicitly incomplete; a visible module is not proof that its workflow is complete.

| Phase | Screen groups |
|---|---|
| 1 — Foundation, authentication and administration | Login/onboarding, tenant administration, workspace, users, roles, branches, profile, themes and audit |
| 2 — Core ERP and financial operations | CRM, customers, sales, purchasing, inventory, finance, reconciliation, budgets and approvals |
| 3 — HR, attendance and payroll | Employees, departments, shifts, attendance, leave, payroll and payslips |
| 4 — Commerce, POS, services and portals | Tenant-scoped storefront/order/return records, POS session sales and cash-close ledger, projects, timesheets, tickets, field jobs and private audited `.txt` uploads; payment and public portals are not connected |
| 5 — AI, automation and production readiness | Safe manual workflows and approval creation, workflow history, configurable status/branch count reports, scoped JSON export/import, custom fields, local record search and branch-scoped API credentials; external AI, signed outbound webhooks and production operations remain open |

### Screen-by-screen screenshots

These 47 captures show the local demo UI with illustrative sample records. The local profile uses demo identity; Keycloak sign-in, email verification and password reset depend on the optional identity services. Module visibility and sample rows do not mean an external provider or production workflow is connected.

<details>
<summary><strong>Phase 1 · Identity, workspace and governance</strong> · 11 screens</summary>

### Audit History

Browse recorded workspace activity for administrative review.

<p><img src="docs/screenshots/governance/audit-history.jpg" alt="Audit History screen" width="100%" /></p>

### Profile & Settings

Review the company profile, regional defaults, appearance and account session.

<p><img src="docs/screenshots/governance/profile-settings.jpg" alt="Profile & Settings screen" width="100%" /></p>

### Roles & Permissions

Review the available roles and the permission scopes attached to each one.

<p><img src="docs/screenshots/governance/roles-permissions.jpg" alt="Roles & Permissions screen" width="100%" /></p>

### Local Sign-up

Create a local demo workspace. This development mode does not create a password account.

<p><img src="docs/screenshots/local-sign-up.jpg" alt="Local Sign-up screen" width="100%" /></p>

### Overview

See workspace activity, key counts and shortcuts into the business modules.

<p><img src="docs/screenshots/overview.jpg" alt="Overview screen" width="100%" /></p>

### Sign In

Branded local demo entry point with owner access and workspace creation options.

<p><img src="docs/screenshots/sign-in.jpg" alt="Sign In screen" width="100%" /></p>

### Sign-out Confirmation

Confirm before leaving the workspace; saved records remain available when you sign in again.

<p><img src="docs/screenshots/sign-out-confirmation.jpg" alt="Sign-out Confirmation screen" width="100%" /></p>

### Branches

Review branch locations and operational assignments for the workspace.

<p><img src="docs/screenshots/workspace/branches.jpg" alt="Branches screen" width="100%" /></p>

### Overview

See workspace activity, key counts and shortcuts into the business modules.

<p><img src="docs/screenshots/workspace/overview.jpg" alt="Overview screen" width="100%" /></p>

### Users & Access

Manage workspace members, access state, roles and branch assignments.

<p><img src="docs/screenshots/workspace/users-access.jpg" alt="Users & Access screen" width="100%" /></p>

### Workspaces

Switch between company workspaces and inspect their status and industry.

<p><img src="docs/screenshots/workspace/workspaces.jpg" alt="Workspaces screen" width="100%" /></p>

</details>

<details>
<summary><strong>Phase 2 · Core ERP and finance</strong> · 11 screens</summary>

### CRM Leads

Track prospective customers, ownership, pipeline status and next sales actions.

<p><img src="docs/screenshots/core-erp/crm-leads-p2.jpg" alt="CRM Leads screen" width="100%" /></p>

### Customers

Browse customer accounts and their contact and relationship details.

<p><img src="docs/screenshots/core-erp/customers-p2.jpg" alt="Customers screen" width="100%" /></p>

### Products & Inventory

Browse the product catalogue, quantities and inventory details.

<p><img src="docs/screenshots/core-erp/products-inventory-p2.jpg" alt="Products & Inventory screen" width="100%" /></p>

### Purchasing

Track supplier orders, expected receipts and purchasing status.

<p><img src="docs/screenshots/core-erp/purchasing-p2.jpg" alt="Purchasing screen" width="100%" /></p>

### Sales & Quotations

Review quotations and sales documents, customer, items, status and branch.

<p><img src="docs/screenshots/core-erp/sales-quotations-p2.jpg" alt="Sales & Quotations screen" width="100%" /></p>

### Suppliers

Maintain supplier records used by purchasing and operational workflows.

<p><img src="docs/screenshots/core-erp/suppliers-p2.jpg" alt="Suppliers screen" width="100%" /></p>

### Approvals

Review pending and completed approval requests across workspace workflows.

<p><img src="docs/screenshots/finance/approvals-p2.jpg" alt="Approvals screen" width="100%" /></p>

### Budgets & Reports

Review illustrative budget totals and finance summaries by reporting period.

<p><img src="docs/screenshots/finance/budgets-reports-p2.jpg" alt="Budgets & Reports screen" width="100%" /></p>

### Invoices & Bills

Review customer invoices and vendor bills, amounts, status and due dates.

<p><img src="docs/screenshots/finance/invoices-bills-p2.jpg" alt="Invoices & Bills screen" width="100%" /></p>

### Payments & Reconciliation

Review manual payment events and invoice reconciliation status.

<p><img src="docs/screenshots/finance/payments-reconciliation-p2.jpg" alt="Payments & Reconciliation screen" width="100%" /></p>

### Sales Document Form

Review the sales document form and its customer, product, quantity and branch fields.

<p><img src="docs/screenshots/record-create-form.jpg" alt="Sales Document Form screen" width="100%" /></p>

</details>

<details>
<summary><strong>Phase 3 · People and payroll</strong> · 7 screens</summary>

### Attendance

Review attendance entries and the recorded check-in and check-out activity.

<p><img src="docs/screenshots/people/attendance-p3.jpg" alt="Attendance screen" width="100%" /></p>

### Departments

Review workspace departments and the teams assigned to each area.

<p><img src="docs/screenshots/people/departments-p3.jpg" alt="Departments screen" width="100%" /></p>

### Employees

Browse employee profiles and their department, branch and employment details.

<p><img src="docs/screenshots/people/employees-p3.jpg" alt="Employees screen" width="100%" /></p>

### Leave Requests

Track leave requests, dates, reasons and approval status.

<p><img src="docs/screenshots/people/leave-requests-p3.jpg" alt="Leave Requests screen" width="100%" /></p>

### My Payslips

Employee self-service view for available payslips and period totals.

<p><img src="docs/screenshots/people/my-payslips-p3.jpg" alt="My Payslips screen" width="100%" /></p>

### Payroll Runs

Review payroll periods, calculated totals and payroll run approval states.

<p><img src="docs/screenshots/people/payroll-runs-p3.jpg" alt="Payroll Runs screen" width="100%" /></p>

### Shifts

Manage shift patterns and view staff schedules configured for operations.

<p><img src="docs/screenshots/people/shifts-p3.jpg" alt="Shifts screen" width="100%" /></p>

</details>

<details>
<summary><strong>Phase 4 · Commerce and operations</strong> · 10 screens</summary>

### POS Sessions

Review point-of-sale sessions, recorded cash activity and close status.

<p><img src="docs/screenshots/commerce/pos-sessions-p4.jpg" alt="POS Sessions screen" width="100%" /></p>

### Promotions

Manage promotion records, active dates and current status.

<p><img src="docs/screenshots/commerce/promotions-p4.jpg" alt="Promotions screen" width="100%" /></p>

### Returns & Refunds

Track return requests and refund review status for store orders.

<p><img src="docs/screenshots/commerce/returns-refunds-p4.jpg" alt="Returns & Refunds screen" width="100%" /></p>

### Store Orders

Review local store orders, customer details and fulfillment status.

<p><img src="docs/screenshots/commerce/store-orders-p4.jpg" alt="Store Orders screen" width="100%" /></p>

### Storefronts

Manage local storefront records and inspect their publishing status.

<p><img src="docs/screenshots/commerce/storefronts-p4.jpg" alt="Storefronts screen" width="100%" /></p>

### Documents

Browse private document metadata and related operational records.

<p><img src="docs/screenshots/operations/documents-p4.jpg" alt="Documents screen" width="100%" /></p>

### Field Jobs

Review field assignments, locations, technicians and completion status.

<p><img src="docs/screenshots/operations/field-jobs-p4.jpg" alt="Field Jobs screen" width="100%" /></p>

### Projects

Track projects, ownership, branch and delivery status in one workspace view.

<p><img src="docs/screenshots/operations/projects-p4.jpg" alt="Projects screen" width="100%" /></p>

### Service Tickets

Track customer service tickets, ownership, priority and resolution status.

<p><img src="docs/screenshots/operations/service-tickets-p4.jpg" alt="Service Tickets screen" width="100%" /></p>

### Timesheets

Review time entries linked to staff and projects for operational follow-up.

<p><img src="docs/screenshots/operations/timesheets-p4.jpg" alt="Timesheets screen" width="100%" /></p>

</details>

<details>
<summary><strong>Phase 5 · Automation and insights</strong> · 8 screens</summary>

### API Clients

Review branch-scoped API client credentials and their access status.

<p><img src="docs/screenshots/automation-insights/api-clients-p5.jpg" alt="API Clients screen" width="100%" /></p>

### Custom Fields

Manage additional workspace fields available to supported record types.

<p><img src="docs/screenshots/automation-insights/custom-fields-p5.jpg" alt="Custom Fields screen" width="100%" /></p>

### Import Jobs

Review structured data imports, their outcomes and validation feedback.

<p><img src="docs/screenshots/automation-insights/import-jobs-p5.jpg" alt="Import Jobs screen" width="100%" /></p>

### Integration Health

Inspect configured integration records and their reported connection health.

<p><img src="docs/screenshots/automation-insights/integration-health-p5.jpg" alt="Integration Health screen" width="100%" /></p>

### Reports

Explore operational report summaries based on workspace records and filters.

<p><img src="docs/screenshots/automation-insights/reports-p5.jpg" alt="Reports screen" width="100%" /></p>

### Workflow Designer

Configure deterministic workflow definitions and the steps available to run.

<p><img src="docs/screenshots/automation-insights/workflow-designer-p5.jpg" alt="Workflow Designer screen" width="100%" /></p>

### Workflow Run History

Review workflow execution history and resulting approval or task records.

<p><img src="docs/screenshots/automation-insights/workflow-run-history-p5.jpg" alt="Workflow Run History screen" width="100%" /></p>

### Workspace Assistant

Search accessible workspace records with the local, permission-scoped assistant.

<p><img src="docs/screenshots/automation-insights/workspace-assistant-p5.jpg" alt="Workspace Assistant screen" width="100%" /></p>

</details>

## Technologies

Target stack from the product brief:

- Web: Next.js App Router, React, TypeScript, Tailwind CSS, accessible shadcn/ui, Lucide, TanStack Query, React Hook Form, Zod and Recharts.
- API: Python, FastAPI, Pydantic, SQLAlchemy, Alembic and PostgreSQL.
- Jobs and cache: Celery and Redis.
- ERP: pinned self-hosted Odoo release with documented edition and addon requirements.
- Identity and files: OIDC provider and S3-compatible private object storage.
- Operations: Docker Compose, GitHub Actions, OpenTelemetry-compatible tracing, Playwright, Pytest and k6.

The current stack uses Next.js, React and TypeScript; FastAPI, SQLAlchemy, Alembic and PostgreSQL; Keycloak; and Odoo 19 Community with a signed Nexora gateway addon. Dependency versions and container tags are pinned. The gateway addon is installed into each newly provisioned tenant database. Tailwind, React Hook Form, Redis, Celery and object storage remain planned, not installed.

## Odoo edition and capability map

Odoo features vary by release, edition and installed addons. No edition or live capability is claimed by this starter. Before implementing a dependent flow, record its model/module, edition, addon/license, integration method and status in [the Odoo capability map](docs/odoo-capabilities.md). Use supported business methods; do not write directly to Odoo business tables with SQL. Financial postings and other atomic operations belong in one Odoo-side transaction.

## Architecture and repository layout

```text
apps/web/app/              Next.js screens, state orchestration and domain helpers
  components/              Overview, settings and record-table UI
  demo-data.ts              Twelve illustrative rows per data module
  modules.ts                Screen registry, phase and field definitions
  workspace.ts              Permission helpers, status options and record normalization
services/api/app/          FastAPI control plane and domain modules
  main.py                   App composition, core ERP and workspace routes
  hr.py, payroll.py         People APIs and pure payroll calculations
  extended.py               Commerce, operations, automation and insight routes
  security.py               OIDC, development and API-client authentication
services/api/migrations/    Alembic schema history and PostgreSQL RLS policies
services/api/tests/        Provider-neutral domain calculation checks
odoo/addons/                Signed Nexora gateway addon
identity/                   Local Keycloak realm and login theme
.vscode/                    Local API and web tasks without Docker
docs/                       Architecture, screens, phases and operations
```

See [architecture](docs/architecture.md) and [developer work split](docs/developer-work-split.md).

## Prerequisites

- Node.js 22.13 or newer and npm for the web application.
- Python 3.11 or newer and PostgreSQL 16 for the local API profile.
- Docker Engine with Compose v2 is optional; it runs the full PostgreSQL, Keycloak, Mailpit, FastAPI and Odoo stack.

For a Docker-free local UI and control-plane preview, use Homebrew PostgreSQL and the VS Code tasks below. Local demo authentication is intentionally limited to development; Odoo posting, Keycloak login/MFA, email delivery and the full ERP setup need their services.

## Installation and local startup

From the repository root, set local secrets and start services:

```bash
cp .env.example .env
# Replace all replace-with-* values in .env with unique random values.
docker compose up -d --build

# In a second terminal:
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`. Create an account and finish email verification and TOTP enrollment, then create a workspace. Local email is captured at `http://localhost:8025`; Keycloak is at `http://localhost:8080`; Odoo is at `http://localhost:8069`; API health is `http://localhost:8000/healthz`. Initial workspace creation provisions an isolated Odoo database and may take a few minutes. Persistent state is stored in Docker volumes.

### VS Code startup without Docker

This development profile uses a local Homebrew PostgreSQL database plus in-process demo identity. It is only suitable for a developer's machine; do not enable `LOCAL_DEMO_MODE` on a shared or deployed API.

```bash
brew services start postgresql@16
createdb nexora_local
cd services/api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd ../../apps/web
npm install
```

Open the repository in VS Code and run **Nexora One: Local (no Docker)** from **Terminal → Run Task**. It starts the API and Next.js together. Open `http://localhost:3000`, choose **Continue as local owner**, then create a local workspace. The database persists in Homebrew PostgreSQL. The demo owner is a fixed local identity with no password prompt, so use this only on a trusted development machine. Odoo backed ERP posting, Keycloak sign-in/MFA, and Mailpit email are not part of this profile.

The local demo also includes 12 illustrative records per data module, saved in browser storage, a generated demo-owner portrait, and three sample PDFs: [invoice](apps/web/public/demo-documents/invoice-nxo-1042.pdf), [purchase order](apps/web/public/demo-documents/purchase-order-nxo-208.pdf), and [team handbook](apps/web/public/demo-documents/team-handbook-sample.pdf). These examples are marked as demo data and are not business transactions. In Keycloak mode, sign-up and password reset run through the identity provider; local demo signup creates a workspace for its fixed demo owner instead of creating a password account.

## Environment configuration

Local service secrets use placeholders in `.env.example`. Never commit `.env`, real credentials, tokens or customer data. Keycloak `start-dev`, local HTTP endpoints and Mailpit are for development only.

The `nexora-one` Keycloak theme applies the N mark and slogan to sign-in, registration, password-reset and required-action screens. New realm imports select it automatically. If `identity-data` already contains the realm, select **nexora-one** for Login Theme and Email Theme under **Realm settings → Themes** in the Keycloak admin console; import does not overwrite an existing realm.

## Database migrations and demo data

The API applies the Alembic baseline migration on startup. Control-plane data is stored in `control-data`; each tenant receives its own Odoo database and filestore in Docker volumes. There are no default accounts or demo passwords.

## API documentation

The API base path is `/api/v1`; local OpenAPI is at `http://localhost:8000/api/v1/openapi.json`. Route boundaries are in [the architecture notes](docs/architecture.md).

## Verification commands

The web package defines `npm run lint` and `npm run build`. Start services with `docker compose up -d --build`; inspect with `docker compose ps` and `docker compose logs api identity odoo`. Automated security and ERP journey checks are still required before either phase can be marked complete.

## Exactly five development phases

1. **Foundation, authentication and administration** — runnable workspace shell, identity, tenancy, provisioning, roles, branches, themes, audit and Odoo connection foundation. In progress.
2. **Core ERP and financial operations** — CRM through orders, purchasing, inventory, finance, reconciliation and approvals. In progress.
3. **HR, attendance and payroll** — employee records, attendance, leave, payroll preparation, approval and self-service.
4. **Commerce, POS, services and portals** — local operational store/order metadata, POS cash close, projects, services and document metadata; checkout and portals need external-facing flows.
5. **AI, automation and production readiness** — deterministic local search, safe manual workflows, scoped JSON/CSV exports, imports, analytics and integration tracking; external AI, delivery and production operations remain open.

Detailed deliverables, dependencies and exit checks are in [docs/phases.md](docs/phases.md). This product has exactly five phases; do not add a sixth.

## Deployment and backup/restore

Production deployment, secrets, backup and restore procedures are not implemented. Phase 5 requires verified deployment and recovery runbooks before a production readiness claim. See [deployment and operations status](docs/deployment.md).

## Integrations

The local Odoo and Keycloak connections are implemented for development. Payment, WhatsApp, courier and external-store providers are not connected. Attendance has a signed generic device-event endpoint with encrypted per-workspace credentials, but no vendor adapter is connected. Each provider must document sandbox/production behavior, secret handling, capabilities, retries and event history in `docs/integrations.md`.

## Known limitations

- Repository was empty before this starter; no legacy application code was present.
- Local identity and Odoo containers are development configuration and need hardening before deployment.
- Payment gateways are not connected. Finance users can register manual payment events and match exact amounts to posted invoices as an audited control-plane reconciliation alternative; this does not post or reconcile an Odoo payment. Stock reservations/transfers and branch-to-warehouse mapping remain incomplete. Confirmed sales orders can create linked draft invoices and full-stock delivery now validates Odoo pickings; received purchase orders can create linked draft vendor bills. These workflows and physical counts against the default Odoo location need runtime verification.
- Payroll prorates effective monthly base, allowances and configured deductions by eligible calendar days, including mid-period hires and salary changes. Approved payroll runs can be exported as audited CSV. The calculation does not apply attendance-based proration, statutory tax or jurisdictional benefits, and payroll payment execution is not connected. The attendance-device endpoint requires a runtime secret and a vendor adapter.
- Invitation resend, company profile and theme preferences persist in the control plane but have not been runtime-verified. Platform administration, security verification, deployment and recovery procedures remain incomplete.
- Phases 4–5 currently use a flexible tenant-RLS resource store for workflows whose external providers are not configured. Store checkout/payment capture, POS-to-Odoo cash posting, inventory-backed fulfillment/returns, portal sessions, rich customer document uploads/scanning, scheduled/background jobs, AI model answers, outbound webhook delivery, industry-pack behavior and backup restore are not implemented. API clients issue branch-scoped, expiring bearer tokens for restricted roles; this local authentication path still needs runtime security verification.
- Odoo 19 Community is pinned. Odoo's external JSON-2 API has subscription restrictions, so the local stack uses a mounted custom addon and ORM methods instead.

## Contributing

1. Read `docs/architecture.md`, `docs/phases.md` and the screen catalogue.
2. Use the ownership map in `docs/developer-work-split.md`; agree on shared contracts before parallel module work.
3. Keep a screen's loading, empty, validation, server-error, access-denied and success behavior with the feature.
4. Mark a capability complete only when behavior, persistence, authorization and appropriate verification meet its exit criteria.
5. Update the phase checklist, API contracts and README status with the implementation.

## License and third-party notices

No license has been selected. The repository owner must choose one before distribution. Preserve all third-party license and addon obligations; see [third-party notices](docs/third-party-notices.md).

## Maintainer

**Raja Haroon Jamal** · [GitHub profile](https://github.com/haroondhanyal) · [Nexora One repository](https://github.com/haroondhanyal/-Nexora-One)
