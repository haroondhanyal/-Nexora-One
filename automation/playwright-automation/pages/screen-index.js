import { OverviewPage } from './overview.page.js';
import { WorkspacesPage } from './workspaces.page.js';
import { UsersPage } from './users.page.js';
import { BranchesPage } from './branches.page.js';
import { RolesPage } from './roles.page.js';
import { AuditPage } from './audit.page.js';
import { SettingsPage } from './settings.page.js';
import { LeadsPage } from './leads.page.js';
import { CustomersPage } from './customers.page.js';
import { SuppliersPage } from './suppliers.page.js';
import { SalesPage } from './sales.page.js';
import { PurchasingPage } from './purchasing.page.js';
import { InventoryPage } from './inventory.page.js';
import { FinancePage } from './finance.page.js';
import { PaymentsPage } from './payments.page.js';
import { BudgetsPage } from './budgets.page.js';
import { ApprovalsPage } from './approvals.page.js';
import { DepartmentsPage } from './departments.page.js';
import { EmployeesPage } from './employees.page.js';
import { ShiftsPage } from './shifts.page.js';
import { AttendancePage } from './attendance.page.js';
import { LeavesPage } from './leaves.page.js';
import { PayrollPage } from './payroll.page.js';
import { PayslipsPage } from './payslips.page.js';
import { StorefrontsPage } from './storefronts.page.js';
import { OrdersPage } from './orders.page.js';
import { PromotionsPage } from './promotions.page.js';
import { ReturnsPage } from './returns.page.js';
import { PosSessionsPage } from './pos_sessions.page.js';
import { ProjectsPage } from './projects.page.js';
import { TimesheetsPage } from './timesheets.page.js';
import { ServiceTicketsPage } from './service_tickets.page.js';
import { FieldJobsPage } from './field_jobs.page.js';
import { DocumentsPage } from './documents.page.js';
import { WorkflowsPage } from './workflows.page.js';
import { WorkflowRunsPage } from './workflow_runs.page.js';
import { ReportsPage } from './reports.page.js';
import { CustomFieldsPage } from './custom_fields.page.js';
import { ApiClientsPage } from './api_clients.page.js';
import { IntegrationHealthPage } from './integration_health.page.js';
import { ImportsPage } from './imports.page.js';
import { AssistantPage } from './assistant.page.js';
import { AuthLoadingPage } from './auth_loading.page.js';
import { AuthErrorPage } from './auth_error.page.js';
import { AuthSignInPage } from './auth_sign_in.page.js';
import { AuthSignUpPage } from './auth_sign_up.page.js';
import { AuthPasswordResetPage } from './auth_password_reset.page.js';
import { WorkspaceSetupPage } from './workspace_setup.page.js';

export { OverviewPage, WorkspacesPage, UsersPage, BranchesPage, RolesPage, AuditPage, SettingsPage, LeadsPage, CustomersPage, SuppliersPage, SalesPage, PurchasingPage, InventoryPage, FinancePage, PaymentsPage, BudgetsPage, ApprovalsPage, DepartmentsPage, EmployeesPage, ShiftsPage, AttendancePage, LeavesPage, PayrollPage, PayslipsPage, StorefrontsPage, OrdersPage, PromotionsPage, ReturnsPage, PosSessionsPage, ProjectsPage, TimesheetsPage, ServiceTicketsPage, FieldJobsPage, DocumentsPage, WorkflowsPage, WorkflowRunsPage, ReportsPage, CustomFieldsPage, ApiClientsPage, IntegrationHealthPage, ImportsPage, AssistantPage, AuthLoadingPage, AuthErrorPage, AuthSignInPage, AuthSignUpPage, AuthPasswordResetPage, WorkspaceSetupPage };

const pageClasses = {
  "overview": OverviewPage,
  "workspaces": WorkspacesPage,
  "users": UsersPage,
  "branches": BranchesPage,
  "roles": RolesPage,
  "audit": AuditPage,
  "settings": SettingsPage,
  "leads": LeadsPage,
  "customers": CustomersPage,
  "suppliers": SuppliersPage,
  "sales": SalesPage,
  "purchasing": PurchasingPage,
  "inventory": InventoryPage,
  "finance": FinancePage,
  "payments": PaymentsPage,
  "budgets": BudgetsPage,
  "approvals": ApprovalsPage,
  "departments": DepartmentsPage,
  "employees": EmployeesPage,
  "shifts": ShiftsPage,
  "attendance": AttendancePage,
  "leaves": LeavesPage,
  "payroll": PayrollPage,
  "payslips": PayslipsPage,
  "storefronts": StorefrontsPage,
  "orders": OrdersPage,
  "promotions": PromotionsPage,
  "returns": ReturnsPage,
  "pos_sessions": PosSessionsPage,
  "projects": ProjectsPage,
  "timesheets": TimesheetsPage,
  "service_tickets": ServiceTicketsPage,
  "field_jobs": FieldJobsPage,
  "documents": DocumentsPage,
  "workflows": WorkflowsPage,
  "workflow_runs": WorkflowRunsPage,
  "reports": ReportsPage,
  "custom_fields": CustomFieldsPage,
  "api_clients": ApiClientsPage,
  "integration_health": IntegrationHealthPage,
  "imports": ImportsPage,
  "assistant": AssistantPage,
  "auth_loading": AuthLoadingPage,
  "auth_error": AuthErrorPage,
  "auth_sign_in": AuthSignInPage,
  "auth_sign_up": AuthSignUpPage,
  "auth_password_reset": AuthPasswordResetPage,
  "workspace_setup": WorkspaceSetupPage,
};

export function screenPageFor(page, screenKey) {
  const PageClass = pageClasses[screenKey];
  if (!PageClass) throw new Error(`No page object registered for screen: ${screenKey}`);
  return new PageClass(page);
}
