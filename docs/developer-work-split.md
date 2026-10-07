# Eight-developer work split

Keep each module independently reviewable. One person owns shared contracts and integration coordination; module owners can work in parallel once API shapes and design tokens are agreed. A person may own adjacent modules where load allows, while review remains cross-team.

| Developer | Primary ownership | Shared outputs |
|---|---|---|
| 1 — Platform and integration lead | Architecture, contracts, CI, release integration, API conventions | OpenAPI, typed client, dependency decisions, merge coordination |
| 2 — Web foundation | App shell, login/onboarding screens, responsive layout, themes and design tokens | Shared UI patterns, accessibility and visual QA |
| 3 — Identity and tenancy | OIDC/session, memberships, provisioning state machine, tenant isolation | Auth contracts, RLS policy and authorization tests |
| 4 — Admin and governance | Company setup, branches, invitations, roles, permissions, profiles and audit | Phase 1 screens and admin endpoints |
| 5 — ERP and finance | CRM, sales, purchasing, inventory, invoices, payments and reports | Odoo mappings and transactional commands |
| 6 — People | Employee records, attendance, leave, payroll and self-service | HR permissions and verified calculation examples |
| 7 — Commerce and operations | Store, POS, projects, service work, documents and external portals | Portal ownership rules and fulfillment contracts |
| 8 — Automation and quality | AI guardrails, workflows, analytics/integrations UI, automation and performance | Playwright/Pytest/k6 coverage and operations evidence |

## Coordination rules

1. Developer 1 publishes API schemas and review notes before parallel endpoint/UI work.
2. Domain owners own their feature folders, backend module, migration and tests together.
3. Shared shell, contracts, permissions and design tokens require owner review before a cross-cutting edit.
4. Integrate behind feature-level routes so the application stays runnable after every phase.
5. Track status in `phases.md`; do not count static screens as completed journeys.
