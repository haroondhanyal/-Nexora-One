import { screenContracts } from './screen-contracts.js';

export const screens = [
  ["overview", "Business overview"], ["workspaces", "Workspaces"], ["users", "Users & access"], ["branches", "Branches"],
  ["roles", "Roles & permissions"], ["audit", "Audit history"], ["settings", "Profile & settings"],
  ["leads", "CRM leads"], ["customers", "Customers"], ["suppliers", "Suppliers"], ["sales", "Sales & quotations"],
  ["purchasing", "Purchasing"], ["inventory", "Products & inventory"], ["finance", "Invoices & bills"],
  ["payments", "Payments & reconciliation"], ["budgets", "Budgets & reports"], ["approvals", "Approvals"],
  ["departments", "Departments"], ["employees", "Employees"], ["shifts", "Shifts"], ["attendance", "Attendance"],
  ["leaves", "Leave requests"], ["payroll", "Payroll runs"], ["payslips", "My payslips"],
  ["storefronts", "Storefronts"], ["orders", "Store orders"], ["promotions", "Promotions"], ["returns", "Returns & refunds"],
  ["pos_sessions", "POS sessions"], ["projects", "Projects"], ["timesheets", "Timesheets"], ["service_tickets", "Service tickets"],
  ["field_jobs", "Field jobs"], ["documents", "Documents"], ["workflows", "Workflow designer"],
  ["workflow_runs", "Workflow run history"], ["reports", "Reports"], ["custom_fields", "Custom fields"],
  ["api_clients", "API clients"], ["integration_health", "Integration health"], ["imports", "Import jobs"],
  ["assistant", "Workspace assistant"],
].map(([key, title]) => ({ key, title, navTitle: key === 'overview' ? 'Overview' : title, ...screenContracts[key] }));

if (screens.length !== 42) throw new Error(`Expected 42 Nexora screens, found ${screens.length}`);
