// Source of truth for the UI → API → database contract of each Nexora screen.
const rows = [
  ['overview','Workspace','workspace/analytics/summary',['workspace_resources','business_records','payroll_runs'],null,'.overview-metrics'],
  ['workspaces','Workspace','me/workspaces',['tenants','memberships'],'Workspace name','.table-panel table'],
  ['users','Workspace','members',['memberships'],'Name','.table-panel table'],
  ['branches','Workspace','branches',['branches'],'Branch name','.table-panel table'],
  ['roles','Governance','roles',[],'Role name','.table-panel table'],
  ['audit','Governance','audit',['audit_events'],'Actor','.table-panel table'],
  ['settings','Governance','company-profile|me/preferences',['tenants','user_preferences'],null,'.theme-grid'],
  ['leads','Core ERP','records/leads',['business_records'],'Lead','.table-panel table'],
  ['customers','Core ERP','records/customers',['business_records'],'Customer','.table-panel table'],
  ['suppliers','Core ERP','records/suppliers',['business_records'],'Supplier','.table-panel table'],
  ['sales','Core ERP','records/sales',['business_records'],'Document','.table-panel table'],
  ['purchasing','Core ERP','records/purchasing',['business_records'],'Purchase order','.table-panel table'],
  ['inventory','Core ERP','records/inventory',['business_records'],'Product','.table-panel table'],
  ['finance','Finance','records/finance',['business_records'],'Document','.table-panel table'],
  ['payments','Finance','records/payments',['business_records'],'Reference','.table-panel table'],
  ['budgets','Finance','records/budgets',['business_records'],'Budget','.table-panel table'],
  ['approvals','Finance','records/approvals',['business_records'],'Request','.table-panel table'],
  ['departments','People','hr/departments',['departments'],'Name','.table-panel table'],
  ['employees','People','hr/employees',['employees'],'Employee no','.table-panel table'],
  ['shifts','People','hr/shifts',['shifts'],'Name','.table-panel table'],
  ['attendance','People','hr/attendance',['attendance'],'Employee','.table-panel table'],
  ['leaves','People','hr/leaves',['leave_requests'],'Employee','.table-panel table'],
  ['payroll','People','hr/payroll/runs',['payroll_runs'],'Period start','.table-panel table'],
  ['payslips','People','hr/payroll/payslips',['payslips'],'Employee','.table-panel table'],
  ['storefronts','Commerce','workspace/storefronts',['workspace_resources'],'Title','.table-panel table'],
  ['orders','Commerce','workspace/orders',['workspace_resources'],'Title','.table-panel table'],
  ['promotions','Commerce','workspace/promotions',['workspace_resources'],'Title','.table-panel table'],
  ['returns','Commerce','workspace/returns',['workspace_resources'],'Title','.table-panel table'],
  ['pos_sessions','Commerce','workspace/pos_sessions',['workspace_resources'],'Title','.table-panel table'],
  ['projects','Operations','workspace/projects',['workspace_resources'],'Title','.table-panel table'],
  ['timesheets','Operations','workspace/timesheets',['workspace_resources'],'Title','.table-panel table'],
  ['service_tickets','Operations','workspace/service_tickets',['workspace_resources'],'Title','.table-panel table'],
  ['field_jobs','Operations','workspace/field_jobs',['workspace_resources'],'Title','.table-panel table'],
  ['documents','Operations','workspace/documents',['workspace_resources','workspace_attachments'],'Title','.table-panel table'],
  ['workflows','Automation & insights','workspace/workflows',['workspace_resources'],'Title','.table-panel table'],
  ['workflow_runs','Automation & insights','workspace/workflow_runs',['workspace_resources'],'Title','.table-panel table'],
  ['reports','Automation & insights','workspace/reports',['workspace_resources'],'Title','.table-panel table'],
  ['custom_fields','Automation & insights','workspace/custom_fields',['workspace_resources'],'Title','.table-panel table'],
  ['api_clients','Automation & insights','workspace/api_clients',['workspace_resources','api_client_credentials'],'Title','.table-panel table'],
  ['integration_health','Automation & insights','workspace/integration_health',['workspace_resources'],'Title','.table-panel table'],
  ['imports','Automation & insights','workspace/imports',['workspace_resources'],'Title','.table-panel table'],
  ['assistant','Automation & insights','workspace/assistant/ask',['workspace_resources'],null,'.page-content .settings-card .settings-form'],
];

export const screenContracts = Object.fromEntries(rows.map(([key,section,api,tables,primaryHeader,primaryLocator]) => [key, {
  key, section, apiPaths: api.split('|').map((path) => `/api/v1/${path}`), tables, primaryHeader, primaryLocator,
  dataSource: tables.length ? `PostgreSQL: ${tables.join(', ')}` : 'Application RBAC policy configuration',
  sidebar: '.nav-item', heading: '.page-heading h1', search: '.search-box input',
}]));

export const sections = Object.values(screenContracts).reduce((groups, contract) => {
  (groups[contract.section] ||= []).push(contract.key);
  return groups;
}, {});

if (Object.keys(screenContracts).length !== 42) throw new Error(`Expected 42 screen contracts, found ${Object.keys(screenContracts).length}`);
