# Screen catalogue

Screen states required everywhere: loading, empty, populated, validation error, server error, access denied and success. External portals always resolve ownership from the authenticated session. Routes below are logical screen names; final URL routing follows the API and identity design.

| Phase | Screen | Primary roles | Main content and actions |
|---|---|---|---|
| 1 | Login | All signed-in roles | Email/password, visibility toggle, remember session, recovery, portal context, theme; authenticate before role-based redirect |
| 1 | Signup and verification | Business owner | Owner/company details, country, timezone, currency, password confirmation, terms and email verification |
| 1 | Recovery and MFA | Account holder | Generic recovery response, expiring reset, MFA challenge and throttling feedback |
| 1 | Workspace chooser | Multi-workspace member | Authorized memberships, company/branch context and last-used workspace |
| 1 | Platform overview | Platform admin | Tenant states, provisioning queue, recent events, plan usage and health |
| 1 | Tenant detail | Platform admin | Owner, plan, database binding, provisioning stages, suspend/retry and support-access expiry |
| 1 | Company overview | Owner/admin | Setup checklist, company profile, branches, members and Odoo connection state |
| 1 | Users and invitations | Owner/admin | Search/filter, invite, resend/revoke, disable, membership and branch assignment |
| 1 | Roles and permissions | Owner/admin | Role list, permission matrix, effective access preview, protected last owner |
| 1 | Branches | Owner/admin | Branch list/detail, timezone/address, member scope and active status |
| 1 | My profile and preferences | Any member | Profile, theme, locale, notifications, security, sessions and sign-out |
| 1 | Audit history | Owner/admin/platform admin | Actor, action, tenant, target, timestamp, request ID and export permission |
| 1 | Odoo connections | Platform admin/owner | Edition/capabilities, test connection, status, error review and safe retry |
| 2 | CRM pipeline and lead detail | Sales | Stages, owner, source, activities, customer link and conversion |
| 2 | Customers and customer detail | Sales/finance | Contacts, addresses, credit context, orders, invoices and notes |
| 2 | Quotation editor/detail | Sales | Items, price/discount/tax validation, approval, send and revision history |
| 2 | Sales orders and fulfillment | Sales/warehouse | Confirmation, reservations, delivery state, invoice link and cancellation rules |
| 2 | Suppliers and purchasing | Purchasing | Supplier records, purchase orders, approvals, receipt and bills |
| 2 | Product catalogue and stock | Inventory | SKU, variants, locations, availability, movement history and adjustment |
| 2 | Transfers and receipts | Warehouse | Source/destination, lot/serial, quantity checks, receipt confirmation |
| 2 | Invoices, bills and expenses | Finance | Draft/review/post, attachments, due state, reversals and approvals |
| 2 | Payments and reconciliation | Finance | Provider events, matching, duplicates, exceptions, safe retry and audit |
| 2 | Budgets and financial reports | Finance/owner | Authorized datasets, filters, branches, export and reconciliation totals |
| 3 | Employee directory and profile | HR/admin | Employment history, department, branch, manager and restricted salary data |
| 3 | Departments and shifts | HR/manager | Org structure, shift schedules, effective dates and assignments |
| 3 | Attendance and corrections | Employee/manager/HR | Clock records, exceptions, evidence, correction request and approval |
| 3 | Leave | Employee/manager/HR | Balances, policy, request, approval and calendar |
| 3 | Payroll run and payslip | Payroll/employee | Snapshot, calculation review, approval, release and own-slip access |
| 4 | Store builder and public storefront | Store admin/shopper | Theme/domain/catalog setup; accessible public product browsing |
| 4 | Cart, checkout and order status | Shopper/customer | Stock check, address, payment state, fulfillment, return/refund status |
| 4 | POS session and close | Cashier/manager | Till opening, sales, payment mix, cash count, variance and close approval |
| 4 | Projects and timesheets | Project staff/manager | Project tasks, time entry, approval and customer billing linkage |
| 4 | Service tickets and field jobs | Technician/manager | Assignment, schedule, checklist, photos/signature and completion evidence |
| 4 | Customer portal | Customer | Own orders, invoices, service status, documents and requests |
| 4 | Supplier portal | Supplier | Own purchase orders, delivery updates and invoice submissions |
| 4 | Employee portal | Employee | Own profile, attendance, leave, released payslips and documents |
| 5 | AI assistant | Authorized staff | Scoped sources, citations, unavailable-data disclosure and approval request |
| 5 | Workflow designer and runs | Owner/admin | Trigger, conditions, allowed actions, run history, failures and safe retry |
| 5 | Analytics and report designer | Owner/manager | Approved fields, filters, branch scope, schedule and protected export |
| 5 | Integration catalogue and events | Admin | Capabilities, secret setup/rotation, sandbox status, event history and retry |
| 5 | API clients and webhooks | Developer/admin | Scopes, one-time token issuance, revocation, signing and delivery logs |
| 5 | Industry pack configuration | Owner/admin | Retail, distribution, e-commerce, services, software, solar and manufacturing workflows |
| 5 | Operations and recovery | Platform ops | Health, queues, backups, restore history, import/export and release status |
