import { endpoints, endpointProfiles } from './catalog/endpoints.js';

// Named read cases keep coverage visible per Nexora screen/module.
const screenReads = [
  ['/branches', 'branches'], ['/members', 'members'], ['/roles', 'roles'], ['/audit', 'audit'],
  ['/records/leads', 'crm-leads'], ['/records/customers', 'customers'], ['/records/suppliers', 'suppliers'],
  ['/records/sales', 'sales'], ['/records/purchasing', 'purchasing'], ['/records/inventory', 'inventory'],
  ['/records/finance', 'finance'], ['/records/payments', 'finance-payments'], ['/records/budgets', 'budgets'],
  ['/records/approvals', 'approvals'], ['/hr/departments', 'departments'], ['/hr/employees', 'employees'],
  ['/hr/shifts', 'shifts'], ['/hr/attendance', 'attendance'], ['/hr/leaves', 'leave-requests'],
  ['/hr/payroll/runs', 'payroll-runs'], ['/hr/payroll/payslips', 'payslips'],
  ['/workspace/storefronts', 'storefronts'], ['/workspace/orders', 'store-orders'], ['/workspace/promotions', 'promotions'],
  ['/workspace/returns', 'returns'], ['/workspace/pos_sessions', 'pos-sessions'], ['/workspace/projects', 'projects'],
  ['/workspace/timesheets', 'timesheets'], ['/workspace/service_tickets', 'service-tickets'], ['/workspace/field_jobs', 'field-jobs'],
  ['/workspace/documents', 'documents'], ['/workspace/workflows', 'workflow-definitions'], ['/workspace/workflow_runs', 'workflow-run-history'],
  ['/workspace/reports', 'saved-reports'], ['/workspace/custom_fields', 'custom-fields'], ['/workspace/api_clients', 'api-clients'],
  ['/workspace/integration_health', 'integration-health'], ['/workspace/imports', 'import-jobs'],
  ['/me/preferences', 'user-preferences'], ['/me/workspaces', 'workspaces'],
];
export const screenEndpointReads = screenReads;

const profiles = ['steady', 'repeat', 'burst', 'recovery', 'consistency'];
const rawCases = [];

for (const [path, screen] of screenReads) {
  for (const profile of profiles) rawCases.push({ method: 'GET', path: `/api/v1${path}`, screen, profile, expectedStatuses: [200], responseKind: 'json' });
}

for (const endpoint of endpoints) {
  const read = endpoint.method === 'GET';
  const endpointRuns = read ? endpointProfiles : ['safe-validation'];
  for (const profile of endpointRuns) {
    const hasResourceId = /\{(?!kind\})[^}]+\}/.test(endpoint.path);
    let expectedStatuses = read ? (hasResourceId || endpoint.safe === 'not-found' ? [200, 404] : [200]) : [400, 404, 422];
    if (endpoint.safe === 'device-auth') expectedStatuses = [400, 401, 403, 404, 422];
    const params = { ...endpoint.params };
    for (const match of endpoint.path.matchAll(/\{([^}]+)\}/g)) {
      if (!params[match[1]]) params[match[1]] = '__K6_RESOURCE_ID__';
    }
    rawCases.push({
      method: endpoint.method,
      path: endpoint.path,
      screen: endpoint.screen,
      profile,
      expectedStatuses,
      responseKind: endpoint.kind,
      root: endpoint.root,
      safe: endpoint.safe,
      params,
      body: read || endpoint.method === 'DELETE' ? undefined : null,
    });
  }
}

export const endpointOperations = endpoints;
export const cases = rawCases.map((testCase, index) => ({
  ...testCase,
  id: `NX-K6-${String(index + 1).padStart(4, '0')}`,
  title: `${testCase.screen} · ${testCase.method} ${testCase.path} · ${testCase.profile}`,
}));

if (cases.length < 300) throw new Error(`Expected broad Nexora K6 coverage, found only ${cases.length} cases`);
