import { copyFile, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { screens as appScreens } from '../config/screens.js';
import { lifecycleScreens } from '../config/lifecycle-screens.js';

const screens = [...appScreens, ...lifecycleScreens];
const databaseScreens = screens.filter((screen) => screen.tables.length > 0);

const root = resolve(new URL('../', import.meta.url).pathname);
const catalogDir = resolve(root, 'catalogs');
const locatorDir = resolve(root, 'locators');
const pageCatalogDir = resolve(catalogDir, 'pages');
const suiteCatalogDir = resolve(catalogDir, 'suites');
const bddFeatureDir = resolve(catalogDir, 'bdd-features');
const executableFeatureDir = resolve(root, 'tests/bdd/features');
const testDir = resolve(root, 'tests');
const sectionDir = resolve(catalogDir, 'sections');
await mkdir(catalogDir, { recursive: true });
await mkdir(locatorDir, { recursive: true });
await mkdir(pageCatalogDir, { recursive: true });
await mkdir(suiteCatalogDir, { recursive: true });
await mkdir(bddFeatureDir, { recursive: true });
await mkdir(executableFeatureDir, { recursive: true });
await mkdir(resolve(testDir, 'api'), { recursive: true });
await mkdir(resolve(testDir, 'bdd'), { recursive: true });
await mkdir(resolve(testDir, 'database'), { recursive: true });
await mkdir(sectionDir, { recursive: true });

const uiPatterns = [
  { category: 'smoke', title: 'Page entry and navigation', action: 'Open the page from its navigation item; check the H1, selected navigation entry, workspace selector, and primary content.' },
  { category: 'smoke', title: 'Primary data renders', action: 'Open the page in a fresh owner session; check its primary content and the expected first table header or overview widget.' },
  { category: 'regression', title: 'Search and clear', action: 'Search for a seeded value, search for an unmatched value, then clear the search; verify the rows return to their initial state.' },
  { category: 'regression', title: 'Create validation and save', action: 'Open the page primary action; verify required fields, save a uniquely named test record, and confirm the row and saved values.' },
  { category: 'regression', title: 'Reload persistence', action: 'Reload after changing a seeded test record; verify the saved status and displayed values remain consistent.' },
  { category: 'integration', title: 'Page to API contract', action: 'Open the page and verify its API contract is mapped to the screen and returns data for the selected workspace.' },
  { category: 'integration', title: 'UI to data persistence', action: 'Change a test record through the page; reload its mapped API data and confirm the same value is returned.' },
  { category: 'integration', title: 'Workspace isolation', action: 'Switch to a second seeded workspace, reopen the page, and verify the first workspace records are not shown.' },
  { category: 'negative', title: 'Required value omitted', action: 'Submit the create form with its required value empty; verify inline validation and confirm no row was written.' },
  { category: 'negative', title: 'Unauthenticated request', action: 'Open the mapped screen request without an owner session; verify access is rejected and private workspace data is absent.' },
];
const ui = [];
const uiGlobalCategoryTotals = { smoke: 0, regression: 0, integration: 0, negative: 0 };
screens.forEach((screen, screenIndex) => {
  const count = screenIndex < (400 % screens.length) ? Math.ceil(400 / screens.length) : Math.floor(400 / screens.length);
  const chosen = uiPatterns.slice(0, 4);
  for (const pattern of chosen) uiGlobalCategoryTotals[pattern.category] += 1;
  while (chosen.length < count) {
    const leastUsed = ['smoke','regression','integration','negative'].sort((a,b) => uiGlobalCategoryTotals[a] - uiGlobalCategoryTotals[b])[0];
    const pattern = uiPatterns.find((p) => p.category === leastUsed && !chosen.includes(p)) || uiPatterns.find((p) => p.category === leastUsed);
    chosen.push(pattern);
    uiGlobalCategoryTotals[leastUsed] += 1;
  }
  for (const pattern of chosen) {
    const caseNumber = ui.length + 1;
    const lifecycleActions = {
      auth_loading: { smoke: 'Open Nexora One and verify the brand splash and session-check progress indicator.', integration: 'Start with a valid and then absent identity session; verify the app routes to the matching account state.' },
      auth_error: { smoke: 'Render the identity-service error state and verify the message and Retry button.', integration: 'Restore the identity service and verify Retry returns the visitor to sign-in.', negative: 'Keep the identity service unavailable; verify retry does not expose private workspace content.' },
      auth_sign_in: { smoke: 'Open the sign-in page and verify the Nexora heading, secure sign-in action and account links.', regression: 'Select Forgot password and Sign up; verify each opens its configured identity flow.', integration: 'Select secure sign-in and verify the configured Keycloak OIDC redirect; in local-demo mode verify owner access works.', negative: 'Make the identity provider unavailable; verify the visitor stays signed out and receives a visible error.' },
      auth_sign_up: { smoke: 'Open the hosted Keycloak registration page and verify its registration form loads.', regression: 'Submit valid test identity data and verify the configured registration/verification response.', integration: 'Complete the configured registration flow and verify the new identity can start workspace setup.', negative: 'Submit invalid or incomplete identity data and verify validation without account creation.' },
      auth_password_reset: { smoke: 'Open the hosted Keycloak password-reset page and verify the email form loads.', regression: 'Submit a valid test email and verify the reset confirmation.', integration: 'Verify password reset returns to the configured sign-in journey.', negative: 'Submit an invalid email and verify validation without disclosing whether an account exists.' },
      workspace_setup: { smoke: 'Open workspace setup and verify company-name input, six industry choices and Create workspace action.', regression: 'Select each industry option and verify the selected choice before submitting.', integration: 'Create a unique test workspace and verify its tenant and owner membership are available after setup.', negative: 'Submit an empty or too-short company name and verify inline validation with no tenant created.' },
    };
    const action = lifecycleActions[screen.key]?.[pattern.category] || pattern.action;
    const expected = lifecycleActions[screen.key]
      ? `The ${screen.title} lifecycle screen behaves as expected: ${action} No unauthorized workspace data is displayed.`
      : pattern.category === 'negative'
      ? 'The page shows an actionable validation or authorization error; no invalid record is persisted and no private tenant data is rendered.'
      : pattern.category === 'integration'
        ? `The page result agrees with ${screen.apiPaths.join(', ')} and its mapped data source (${screen.tables.join(', ') || 'RBAC policy'}), scoped to the active workspace.`
        : pattern.title === 'Create validation and save'
          ? `A unique test record is saved once in the active workspace; the ${screen.primaryHeader || 'primary page content'} shows its submitted values.`
          : `The ${screen.title} page shows its expected heading, active navigation and ${screen.primaryHeader ? `table headed “${screen.primaryHeader}”` : 'primary overview content'} without horizontal overflow.`;
    const publicLifecycle = ['auth_loading','auth_error','auth_sign_in','auth_sign_up','auth_password_reset'].includes(screen.key);
    const navigationStep = screen.key === 'auth_loading' ? 'Load the Nexora app entry route.' : screen.key === 'auth_error' ? 'Simulate an identity-provider initialization error.' : screen.key === 'auth_sign_in' ? 'Reach the signed-out Nexora sign-in screen.' : screen.key === 'auth_sign_up' ? 'Open Sign up from the signed-out page using a configured identity provider.' : screen.key === 'auth_password_reset' ? 'Open Forgot password from the signed-out page using a configured identity provider.' : screen.key === 'workspace_setup' ? 'Sign in locally and choose Create a demo workspace.' : `Navigate to ${screen.title} using ${screen.navTitle}.`;
    const expectedContent = screen.primaryHeader ? `the ${screen.primaryHeader} column` : publicLifecycle || screen.key === 'workspace_setup' ? 'the page-specific heading and primary control' : 'the primary content';
    ui.push({ id: `NX-UI-${String(caseNumber).padStart(3, '0')}`, page: screen.title, pageKey: screen.key, section: screen.section, category: pattern.category, difficulty: ['integration','negative'].includes(pattern.category) ? 'high' : 'standard', title: `${screen.title} · ${pattern.category} · ${pattern.title}`, preconditions: `${publicLifecycle ? 'Signed-out visitor or controlled identity-provider state' : screen.key === 'workspace_setup' ? 'Owner starts with no active tenant' : `Owner session; seeded test workspace; page API ${screen.apiPaths.join(', ')}`}; backing data ${screen.tables.join(', ') || screen.dataSource || 'none'}.`, steps: [navigationStep, action, `Check ${expectedContent} and confirm no private data is exposed to the wrong account.`], expected, locatorFile: `locators/${screen.key}.json`, evidence: 'Capture screenshot on failure; retain Playwright video and trace on failure.' });
  }
});

const apiVariants = [
  { kind: 'success', method: 'GET', expected: '200 JSON; response has the documented collection or resource shape.' },
  { kind: 'missing-auth', method: 'GET', expected: '401; response does not disclose tenant data.' },
  { kind: 'missing-tenant', method: 'GET', expected: '4xx; request without X-Tenant-ID is rejected.' },
  { kind: 'wrong-tenant', method: 'GET', expected: '403 or empty tenant-scoped result; no foreign tenant records are exposed.' },
  { kind: 'content-type', method: 'GET', expected: '200 JSON with an application/json content type.' },
];
const endpoints = [...new Map(screens.flatMap((s) => s.apiPaths.map((path) => [path, { path, screen: s }]))).values()];
const api = Array.from({ length: 200 }, (_, i) => {
  const endpoint = endpoints[i % endpoints.length];
  const variant = apiVariants[Math.floor(i / endpoints.length) % apiVariants.length];
  const method = endpoint.path.endsWith('/assistant/ask') ? 'POST' : variant.method;
  const expected = method === 'POST' && variant.kind === 'success' ? '200 JSON; response contains the assistant answer and source metadata.' : variant.expected;
  return { id: `NX-API-${String(i + 1).padStart(3, '0')}`, page: endpoint.screen.title, pageKey: endpoint.screen.key, difficulty: ['wrong-tenant','missing-auth','missing-tenant'].includes(variant.kind) ? 'high' : 'standard', title: `${variant.kind} · ${method} ${endpoint.path} · ${endpoint.screen.title}`, method, path: endpoint.path, headers: variant.kind === 'missing-auth' ? { Accept: 'application/json' } : { Authorization: 'Bearer <test-token>', 'X-Tenant-ID': '<disposable-test-tenant>', Accept: 'application/json' }, body: method === 'POST' ? { question: 'List sample projects', sources: ['projects'] } : null, expected, requestLog: `Record case ID, method, path, tenant ID (masked), status, elapsed milliseconds, correlation/request ID, and response validation; never log bearer tokens or personal data.`, evidence: 'Attach sanitized request/response log and Playwright trace on failure.' };
});

const bdd = Array.from({ length: 200 }, (_, i) => {
  const screen = screens[i % screens.length];
  const n = Math.floor(i / screens.length);
  const pageVerbs = {
    auth_loading: [['a visitor opens Nexora One', 'the branded loading state appears while session status is checked'], ['the identity session is valid', 'the visitor is routed to their authorized workspace'], ['the identity session is absent', 'the sign-in screen appears after initialization'], ['the session check is still pending', 'the loading progress remains visible without flashing private content'], ['the session check completes', 'the loading state exits and a stable account state is rendered']],
    auth_error: [['the identity provider is unavailable', 'a clear service error and retry action are shown'], ['the identity provider becomes available', 'retry reloads the authentication check'], ['the identity provider remains unavailable after retry', 'the error remains visible and the visitor stays signed out'], ['the identity provider recovers after a failed attempt', 'retry reaches the sign-in screen'], ['a signed-out visitor opens the error route', 'no workspace content or private data is shown']],
    auth_sign_in: [['an owner selects secure sign-in', 'the browser starts the configured Keycloak OIDC flow'], ['a local demo owner selects continue', 'the local demo workspace opens without requesting a password'], ['a visitor selects forgot password', 'the configured identity-provider reset flow opens'], ['a visitor selects sign-up', 'the configured identity-provider registration flow opens'], ['the identity provider rejects authentication', 'the visitor remains signed out and receives the configured identity error']],
    auth_sign_up: [['a visitor submits valid registration details', 'the identity provider accepts the details or displays its configured verification step'], ['a visitor submits invalid registration details', 'field-level validation is shown and no account is created'], ['a visitor uses an email already registered', 'the provider displays its safe duplicate-account response'], ['a visitor submits mismatched password confirmation', 'password confirmation validation prevents submission'], ['a visitor completes email verification', 'the verified account can continue to Nexora workspace setup']],
    auth_password_reset: [['a user submits a registered email', 'the identity provider displays its configured reset confirmation without revealing account existence'], ['a user submits an invalid email', 'the email field validation is displayed'], ['a user submits an unregistered email', 'the same safe confirmation is shown without account enumeration'], ['a user opens an expired reset link', 'the provider offers a safe retry path without changing the password'], ['a user completes a valid reset link', 'the new password is accepted and sign-in is available']],
    workspace_setup: [['the owner submits a valid company name and industry', 'one workspace and its initial owner membership are created'], ['the owner submits an empty company name', 'required-field validation appears and no workspace is created'], ['the owner selects a different industry', 'the selected industry is shown as the active choice before submission'], ['the owner submits a company name below the minimum length', 'validation appears and no tenant is created'], ['the owner submits a valid workspace twice', 'idempotency or duplicate handling prevents an unintended second tenant']],
  };
  const verbs = pageVerbs[screen.key] || [
    ['an owner opens the page', 'the page heading and primary content are visible'],
    ['the owner searches for a known record', 'the matching record is shown and unrelated records are hidden'],
    ['the owner submits valid required fields', 'the record is saved and displayed in the active workspace'],
    ['the owner omits a required field', 'field validation appears and the record is not saved'],
    ['the owner changes to another workspace', 'only data belonging to the selected workspace is shown'],
  ];
  const [when, then] = verbs[n % verbs.length];
  const authenticated = ['auth_loading','auth_error','auth_sign_in','auth_sign_up','auth_password_reset'].includes(screen.key);
  const mapping = screen.apiPaths.length ? `the screen API ${screen.apiPaths.join(', ')}` : screen.dataSource || 'the Nexora identity lifecycle';
  const dataMapping = screen.tables.length ? `the data tables ${screen.tables.join(', ')}` : screen.testability === 'External identity provider page' ? 'the configured Keycloak identity provider' : 'the configured identity/session state';
  return { id: `NX-BDD-${String(i + 1).padStart(3, '0')}`, feature: `${screen.title} workflow`, page: screen.title, pageKey: screen.key, scenario: `${screen.title}: ${when}`, given: `Given ${authenticated ? 'a visitor is on the Nexora account lifecycle' : 'the Nexora owner is authenticated or is creating a workspace'}`, when: `When ${when}`, then: `Then ${then}`, and: `And the result is consistent with ${mapping} and ${dataMapping}`, testData: screen.key === 'workspace_setup' ? 'Use a unique company name with valid industry; delete the test tenant and membership after verification.' : 'Use the configured test identity only; do not use real customer credentials.' };
});

const dbActions = ['select tenant-scoped rows', 'insert a valid fixture row', 'update the fixture row with the current version', 'delete the fixture row', 'reject a row with a missing required value', 'reject a duplicate business key', 'rollback a transaction after a failed write', 'deny a cross-tenant read', 'deny a cross-tenant update', 'verify foreign-key references', 'verify timestamp and status persistence', 'confirm cleanup removes the fixture'];
const db = Array.from({ length: 1000 }, (_, i) => {
  const screen = databaseScreens[i % databaseScreens.length];
  const action = dbActions[Math.floor(i / screens.length) % dbActions.length];
  const table = screen.tables[0] || 'RBAC policy configuration';
  const mutating = /insert|update|delete|rollback/.test(action);
  return { id: `NX-DB-${String(i + 1).padStart(4, '0')}`, page: screen.title, pageKey: screen.key, difficulty: /cross-tenant|rollback|foreign-key/.test(action) ? 'high' : 'standard', table, action, context: `Disposable PostgreSQL test database; non-superuser role; tenant A owns the fixture; tenant B is an unrelated control; transaction ${mutating ? 'must roll back or clean up' : 'is read-only'}.`, data: { tenant_id: '<test-tenant-A>', fixture_key: `NX-DB-${String(i + 1).padStart(4, '0')}`, source: screen.key, sample_payload: { label: `${screen.title} fixture`, status: 'test' } }, steps: [`Arrange the documented fixture in ${table}.`, `Execute action: ${action}.`, 'Read the affected row through the application role and verify tenant ownership, persisted values, and audit fields.', 'Rollback or delete the fixture and verify cleanup.'], expected: action.includes('cross-tenant') ? 'RLS or API authorization blocks access; tenant B receives no tenant A row.' : action.includes('reject') || action.includes('deny') ? 'Operation is rejected with the expected constraint or authorization error and leaves stored data unchanged.' : 'Database state matches the requested operation; tenant scope, version, and cleanup are verified.', transaction: 'BEGIN; use unique fixture key; ROLLBACK in finally; never point at production.', logging: 'Record case ID, database/schema/table, masked tenant, operation, row count, SQLSTATE, elapsed time, and rollback status; exclude credentials and personal data.' };
});

const locators = {};
for (const s of screens) {
  const contract = s;
  const role = (role, options = {}) => ({ type: 'role', role, ...options });
  const css = (selector) => ({ type: 'css', selector });
  const appMap = {
    pageHeading: role('heading', { level: 1 }),
    sidebarItem: role('button', { name: s.navTitle }),
    primaryContent: contract.primaryHeader ? role('table') : css(contract.primaryLocator),
    globalSearch: { type: 'placeholder', value: 'Search records...' },
    workspaceSwitcher: role('button', { name: 'Workspace:', exact: false }),
    table: role('table'),
    tableHeader: role('columnheader'),
    tableRows: css('tbody tr'),
    primaryAction: s.key === 'projects' ? role('button', { name: 'Add project', exact: true }) : css('.page-heading button'),
    form: css('form.record-dialog'),
    validation: css('[aria-invalid="true"], [role="alert"]'),
  };
  const lifecycleMaps = {
    auth_loading: { brandMark: css('.brand-splash img'), pageTitle: role('heading', { name: 'Nexora One', level: 1 }), progress: css('.brand-splash-progress') },
    auth_error: { brandMark: css('.brand-splash img'), errorMessage: css('.brand-splash-error'), retryButton: role('button', { name: 'Retry' }) },
    auth_sign_in: { pageTitle: role('heading', { name: 'Sign in to Nexora One', level: 2 }), signInButton: css('.setup-submit'), resetPasswordLink: role('button', { name: 'Forgot password?' }), signUpButton: role('button', { name: 'Sign up' }), localDemoNote: css('.auth-security-note') },
    auth_sign_up: { identityProviderForm: 'form', username: 'input[name="username"]', email: 'input[name="email"]', password: '#password', visiblePassword: '#password:visible', submit: 'input[type="submit"]' },
    auth_password_reset: { identityProviderForm: 'form', email: 'input[name="username"]', submit: 'input[type="submit"]' },
    workspace_setup: { pageTitle: role('heading', { name: 'Start with your business', level: 2 }), companyName: '#workspace-name', industryOptions: role('radio'), createWorkspaceButton: role('button', { name: 'Create workspace' }), validation: css('[aria-invalid="true"], [role="alert"]') },
  };
  const map = lifecycleMaps[s.key] || appMap;
  locators[s.key] = { page: s.title, pageKey: s.key, section: s.section, navigationLabel: s.navTitle, expectedHeading: s.title, expectedFirstColumn: s.primaryHeader, apiPaths: s.apiPaths, dataTables: s.tables, strategy: 'Prefer Playwright role, label, placeholder and text locators. Use ID selectors for unique fields and CSS selectors only for stable layout containers.', selectors: map };
  await writeFile(resolve(locatorDir, `${s.key}.json`), `${JSON.stringify(locators[s.key], null, 2)}\n`);
}

const uiCategoryTotals = Object.fromEntries(['smoke','regression','integration','negative'].map((category) => [category, ui.filter((row) => row.category === category).length]));
const catalog = { product: 'Nexora One', generatedAt: new Date().toISOString(), executionStatus: 'catalog-only; results are recorded only after the corresponding suites run', totals: { ui: ui.length, api: api.length, bdd: bdd.length, database: db.length }, uiCategoryTotals, pageCount: screens.length, pageInventory: screens.map(({ key, title, section, testability }) => ({ key, title, section, testability: testability || 'Nexora app' })), suites: { ui, api, bdd, database: db }, locatorFiles: Object.fromEntries(screens.map((s) => [s.key, `locators/${s.key}.json`])) };
if (ui.length !== 400 || api.length !== 200 || bdd.length !== 200 || db.length !== 1000) throw new Error('Case catalog count mismatch');
await writeFile(resolve(testDir, 'api/cases.json'), `${JSON.stringify({ suite: 'API', executionStatus: 'definitions; run api-contract.spec.js for executable checks', total: api.length, cases: api }, null, 2)}\n`);
await writeFile(resolve(testDir, 'bdd/cases.json'), `${JSON.stringify({ suite: 'BDD', format: 'Gherkin feature files', total: bdd.length, cases: bdd }, null, 2)}\n`);
await writeFile(resolve(testDir, 'database/cases.json'), `${JSON.stringify({ suite: 'Database', executionStatus: 'definitions; run database-persistence.spec.js for executable checks', total: db.length, cases: db }, null, 2)}\n`);
for (const category of ['smoke','regression','integration','negative']) {
  const categoryDir = resolve(testDir, 'ui', category);
  await mkdir(categoryDir, { recursive: true });
  const cases = ui.filter((row) => row.category === category);
  await writeFile(resolve(categoryDir, 'cases.json'), `${JSON.stringify({ suite: `UI ${category}`, executionStatus: 'case definitions; executable specs are in this folder', total: cases.length, cases }, null, 2)}\n`);
}
await writeFile(resolve(catalogDir, 'case-catalog.json'), `${JSON.stringify(catalog, null, 2)}\n`);
for (const [suite, rows] of Object.entries(catalog.suites)) {
  await writeFile(resolve(suiteCatalogDir, `${suite}.json`), `${JSON.stringify(rows, null, 2)}\n`);
}
for (const category of ['smoke','regression','integration','negative']) {
  const categoryDir = resolve(suiteCatalogDir, 'ui');
  await mkdir(categoryDir, { recursive: true });
  const rows = ui.filter((row) => row.category === category);
  await writeFile(resolve(categoryDir, `${category}.json`), `${JSON.stringify(rows, null, 2)}\n`);
}
for (const screen of screens) {
  const pageCases = Object.fromEntries(Object.entries(catalog.suites).map(([suite, rows]) => [suite, rows.filter((row) => row.pageKey === screen.key)]));
  const mappingText = [screen.apiPaths.length ? `API ${screen.apiPaths.join(', ')}` : null, screen.tables.length ? `database tables ${screen.tables.join(', ')}` : screen.dataSource || null].filter(Boolean).join('; ') || 'client-side authentication lifecycle';
  await writeFile(resolve(pageCatalogDir, `${screen.key}.json`), `${JSON.stringify({ page: screen.title, pageKey: screen.key, section: screen.section, locatorFile: `../../locators/${screen.key}.json`, apiPaths: screen.apiPaths, dataTables: screen.tables, caseCounts: Object.fromEntries(Object.entries(pageCases).map(([key, rows]) => [key, rows.length])), cases: pageCases }, null, 2)}\n`);
  const scenarios = pageCases.bdd.map((row) => `  Scenario: ${row.id} ${row.scenario}\n    ${row.given}\n    ${row.when}\n    ${row.then}\n    ${row.and}`).join('\n\n');
  const feature = `Feature: ${screen.title} (${screen.section})\n  Nexora page behavior mapped to ${mappingText}.\n\n${scenarios}\n`;
  await writeFile(resolve(bddFeatureDir, `${screen.key}.feature`), feature);
  await writeFile(resolve(executableFeatureDir, `${screen.key}.feature`), feature);
}
const requests = ['@apiBase = http://127.0.0.1:8000/api/v1', '@token = replace-with-disposable-test-token', '@tenantId = replace-with-disposable-test-tenant'];
for (const row of api) {
  const kind = row.title.split(' · ')[0];
  requests.push(`\n### ${row.id} | ${row.title}\n${row.method} {{apiBase}}${row.path.replace('/api/v1','')}\nAccept: application/json\nX-Correlation-ID: ${row.id}`);
  if (kind !== 'missing-auth') requests.push('Authorization: Bearer {{token}}');
  if (kind !== 'missing-tenant') requests.push('X-Tenant-ID: {{tenantId}}');
  if (row.body) requests.push('Content-Type: application/json\n\n' + JSON.stringify(row.body, null, 2));
  requests.push(`\n\n# Expected: ${row.expected}\n# Log: ${row.requestLog}`);
}
await writeFile(resolve(catalogDir, 'api-requests.http'), `${requests.join('\n')}\n`);
const html = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · Case Catalog</title><style>body{margin:0;background:#f4f6fa;color:#17243b;font:13px/1.5 system-ui}header{background:white;padding:16px 4%;border-bottom:1px solid #e5eaf2;display:flex;gap:20px}a{color:#4169d8}.wrap{max-width:1450px;margin:auto;padding:24px 3%}h1{margin:0 0 4px}.muted{color:#758196}.cards{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.card{padding:12px 16px;background:white;border:1px solid #e5eaf2;border-radius:9px}.card b{display:block;font-size:20px;color:#4169d8}.filters{display:flex;gap:8px;margin:15px 0}.filters input,.filters select{padding:9px;border:1px solid #dce3ed;border-radius:7px;background:white}.filters input{flex:1}table{width:100%;border-collapse:collapse;background:white;font-size:11px}td,th{padding:9px;border-bottom:1px solid #e8edf3;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#f9fafc}td details{min-width:180px;max-width:650px}code{white-space:pre-wrap;overflow-wrap:anywhere}.table{overflow:auto;max-height:72vh;border:1px solid #e5eaf2;border-radius:9px}.warning{padding:10px 12px;background:#fff5d9;border-radius:8px}</style><header><b>Nexora One · QA</b><a href="/">Report center</a><a href="/screenshots/index.html">Screenshots</a><a href="/evidence/">Hard case evidence</a></header><main class="wrap"><h1>Test case catalog</h1><div class="muted">1,800 detailed cases mapped to all 42 application pages and page-specific locator files.</div><p class="warning">Catalog definitions are planned coverage. A case shows a pass/fail result only after its executable suite records a run.</p><section id="cards" class="cards"></section><div class="filters"><input id="q" placeholder="Search case, page, action, or data"><select id="suite"><option value="">All suites</option><option value="ui">UI</option><option value="api">API</option><option value="bdd">BDD</option><option value="database">Database</option></select><select id="page"><option value="">All pages</option>${screens.map((s)=>`<option value="${s.key}">${s.title}</option>`).join('')}</select></div><div class="table"><table><thead><tr><th>ID</th><th>Suite</th><th>Page</th><th>Case / action</th><th>Request, steps, context and expected result</th></tr></thead><tbody id="rows"></tbody></table></div></main><script type="application/json" id="catalog">${JSON.stringify(catalog).replaceAll('<','\\u003c')}</script><script>const c=JSON.parse(document.querySelector('#catalog').textContent),names={ui:'UI',api:'API',bdd:'BDD',database:'DB'},all=Object.entries(c.suites).flatMap(([suite,rows])=>rows.map(x=>({...x,suite})));document.querySelector('#cards').innerHTML=Object.entries(c.totals).map(([k,v])=>'<div class="card"><b>'+v+'</b>'+names[k]+' cases</div>').join('');const q=document.querySelector('#q'),suite=document.querySelector('#suite'),page=document.querySelector('#page'),tbody=document.querySelector('#rows');function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function details(x){return Object.entries(x).filter(([k])=>!['id','suite','page','pageKey','title'].includes(k)).map(([k,v])=>'<b>'+esc(k)+'</b>: <code>'+esc(typeof v==='object'?JSON.stringify(v,null,2):v)+'</code>').join('<br>')}function draw(){const query=q.value.toLowerCase(),rows=all.filter(x=>(!suite.value||x.suite===suite.value)&&(!page.value||x.pageKey===page.value)&&(!query||JSON.stringify(x).toLowerCase().includes(query)));document.querySelector('.muted').textContent=rows.length+' of '+all.length+' catalog cases · 42 pages · '+c.executionStatus;tbody.innerHTML=rows.map(x=>'<tr><td>'+esc(x.id)+'</td><td>'+esc(names[x.suite])+'</td><td>'+esc(x.page)+'</td><td>'+esc(x.title||x.scenario||x.action||x.method+' '+x.path)+'</td><td><details><summary>Details</summary>'+details(x)+'</details></td></tr>').join('')}q.oninput=suite.onchange=page.onchange=draw;draw();</script></html>`;
let catalogHtml = html
  .replace('1,800 detailed cases mapped to all 42 application pages and page-specific locator files.', `1,800 detailed cases mapped to all ${screens.length} Nexora app and account lifecycle screens with page-specific locator files.`)
  .replace("+' · 42 pages · '+c.executionStatus", `+' · ${screens.length} pages · '+c.executionStatus`)
  .replace('<header><b>Nexora One · QA</b><a href="/">Report center</a><a href="/screenshots/index.html">Screenshots</a><a href="/evidence/">Hard case evidence</a></header>', `<header><b>Nexora One · QA</b><a href="/">Report center</a><a href="/catalog/sections/ui.html">UI</a><a href="/catalog/sections/api.html">API</a><a href="/catalog/sections/bdd.html">BDD Cucumber</a><a href="/catalog/sections/database.html">DB Testing</a><a href="/screenshots/index.html">Screenshots</a><a href="/evidence/">Hard case evidence</a></header>`)
  .replace('<section id="cards" class="cards"></section>', '<section id="cards" class="cards"></section><h2>UI coverage by type</h2><section id="ui-categories" class="cards"></section>')
  .replace('<div class="filters">', '<div class="filters"><select id="category"><option value="">All UI categories</option><option value="smoke">Smoke</option><option value="regression">Regression</option><option value="integration">Integration</option><option value="negative">Negative</option></select>')
  .replace("const q=document.querySelector('#q'),suite=document.querySelector('#suite'),page=document.querySelector('#page'),tbody=document.querySelector('#rows');", "document.querySelector('#ui-categories').innerHTML=Object.entries(c.uiCategoryTotals).map(([k,v])=>'<div class=\\\"card\\\"><b>'+v+'</b>UI '+k+'</div>').join('');const q=document.querySelector('#q'),suite=document.querySelector('#suite'),page=document.querySelector('#page'),category=document.querySelector('#category'),tbody=document.querySelector('#rows');")
  .replace("(!page.value||x.pageKey===page.value)&&(!query", "(!page.value||x.pageKey===page.value)&&(!category.value||x.category===category.value)&&(!query")
  .replace('q.oninput=suite.onchange=page.onchange=draw;', 'q.oninput=suite.onchange=page.onchange=category.onchange=draw;');
await writeFile(resolve(catalogDir, 'index.html'), catalogHtml);
const evidenceDir = resolve(root, 'evidence');
await mkdir(evidenceDir, { recursive: true });
for (const screen of appScreens) {
  const source = resolve(root, 'screenshots/runs', `${screen.key}.png`);
  const caseRow = ui.find((row) => row.pageKey === screen.key && row.category === 'integration');
  const targetName = `${caseRow.id}-${screen.key}.png`;
  try {
    await copyFile(source, resolve(evidenceDir, targetName));
    caseRow.evidence = `evidence/${targetName} · existing per-screen Playwright capture`;
    caseRow.evidenceAvailable = true;
  } catch {
    caseRow.evidenceAvailable = false;
  }
}
await writeFile(resolve(catalogDir, 'case-catalog.json'), `${JSON.stringify(catalog, null, 2)}\n`);
const currentCatalogHtml = await readFile(resolve(catalogDir, 'index.html'), 'utf8');
const embeddedCatalog = JSON.stringify(catalog).replaceAll('<', '\\u003c');
await writeFile(resolve(catalogDir, 'index.html'), currentCatalogHtml.replace(/(<script type="application\/json" id="catalog">)[\s\S]*?(<\/script>)/, `$1${embeddedCatalog}$2`));
const evidenceFiles = (await readdir(evidenceDir)).filter((f) => /\.(png|jpe?g|webp|webm|mp4)$/i.test(f));
const media = evidenceFiles.map((file) => `<figure><${/\.(webm|mp4)$/i.test(file) ? 'video controls' : 'img'} src="${encodeURIComponent(file)}" ${/\.(webm|mp4)$/i.test(file) ? '' : 'alt="Hard case screenshot"'}></${/\.(webm|mp4)$/i.test(file) ? 'video' : 'img'}><figcaption>${file}</figcaption></figure>`).join('');
await writeFile(resolve(evidenceDir, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · Hard Case Evidence</title><style>body{font:14px system-ui;background:#f4f6fa;color:#17243b;margin:0}header,main{padding:18px 4%}header{background:white;display:flex;gap:20px}a{color:#4169d8}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}figure{margin:0;padding:10px;background:white;border:1px solid #e5eaf2;border-radius:9px}img,video{width:100%;max-height:460px;object-fit:contain;background:#101827}figcaption{font-size:11px;padding-top:7px;overflow-wrap:anywhere}.note{color:#758196}</style><header><b>Nexora One · QA evidence</b><a href="/">Report center</a><a href="/catalog/">Case catalog</a></header><main><h1>Hard case screenshots and videos</h1><p class="note">Place reviewed screenshots (.png/.jpg/.webp) and recordings (.webm/.mp4) here. Playwright retains failure videos and traces under test-results; copy selected recordings here with their case ID in the filename. Evidence appears here on the next catalog build.</p><section class="grid">${media || '<p class="note">No hard-case media has been attached yet. Existing product reference screenshots are in the Screenshots gallery.</p>'}</section></main></html>`);
const sectionNav = `<nav><a href="/catalog/">All cases</a><a href="/catalog/sections/ui.html">UI · ${ui.length}</a><a href="/catalog/sections/api.html">API · ${api.length}</a><a href="/catalog/sections/bdd.html">BDD Cucumber · ${bdd.length}</a><a href="/catalog/sections/database.html">DB testing · ${db.length}</a></nav>`;
const sectionStyles = `body{margin:0;background:#f4f6fa;color:#17243b;font:13px/1.5 system-ui}header,.wrap{padding:17px 4%}header{background:white;display:flex;gap:14px;align-items:center;flex-wrap:wrap;border-bottom:1px solid #e5eaf2}nav{display:flex;gap:12px;flex-wrap:wrap}a{color:#4169d8}.wrap{max-width:1450px;margin:auto}h1{margin:0}.muted{color:#758196}.filters{display:flex;gap:8px;margin:14px 0}.filters input,.filters select{padding:9px;border:1px solid #dce3ed;border-radius:7px;background:white}.filters input{flex:1}.table{overflow:auto;max-height:74vh;border:1px solid #e5eaf2;border-radius:9px}table{width:100%;border-collapse:collapse;background:white;font-size:11px}td,th{padding:9px;border-bottom:1px solid #e8edf3;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#f9fafc}details{max-width:700px}code{white-space:pre-wrap;overflow-wrap:anywhere}.pill{display:inline-block;margin:4px;padding:8px 12px;background:white;border:1px solid #e5eaf2;border-radius:8px}aside{padding:10px;background:#fff5d9;border-radius:8px;margin:12px 0}`;
function sectionPage({ title, suite, rows, extras = '' }) {
  const payload = JSON.stringify(rows).replaceAll('<', '\\u003c');
  const categoryOptions = suite === 'ui' ? `<select id="category"><option value="">All UI types</option>${['smoke','regression','integration','negative'].map((x)=>`<option value="${x}">${x}</option>`).join('')}</select>` : '';
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · ${title}</title><style>${sectionStyles}</style><header><b>Nexora One · QA</b>${sectionNav}</header><main class="wrap"><h1>${title}</h1><p class="muted">${rows.length} detailed case records across ${screens.length} Nexora screens. Results remain pending until an executable run records them.</p>${extras}<div class="filters"><input id="q" placeholder="Search cases, steps, table, request or expected result">${categoryOptions}<select id="page"><option value="">All pages</option>${screens.map((s)=>`<option value="${s.key}">${s.title} · ${s.section}</option>`).join('')}</select></div><div class="table"><table><thead><tr><th>Case ID</th><th>Page</th><th>Type / action</th><th>Details and expected result</th></tr></thead><tbody id="rows"></tbody></table></div></main><script type="application/json" id="cases">${payload}</script><script>const rows=JSON.parse(document.querySelector('#cases').textContent),q=document.querySelector('#q'),page=document.querySelector('#page'),category=document.querySelector('#category'),body=document.querySelector('#rows');function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function title(x){return x.title||x.scenario||x.action||x.method+' '+x.path}function details(x){return Object.entries(x).filter(([k])=>!['id','page','pageKey','title','category','scenario','action'].includes(k)).map(([k,v])=>'<b>'+esc(k)+'</b>: <code>'+esc(typeof v==='object'?JSON.stringify(v,null,2):v)+'</code>').join('<br>')}function render(){const term=q.value.toLowerCase(),found=rows.filter(x=>(!page.value||x.pageKey===page.value)&&(!category||!category.value||x.category===category.value)&&(!term||JSON.stringify(x).toLowerCase().includes(term)));body.innerHTML=found.map(x=>'<tr><td>'+esc(x.id)+'</td><td>'+esc(x.page)+'</td><td>'+esc(x.category||x.action||x.method+' '+x.path)+'</td><td><details><summary>'+esc(title(x))+'</summary>'+details(x)+(x.pageKey?'<p><a href="/locators/'+esc(x.pageKey)+'.json">Open page locator map</a></p>':'')+'</details></td></tr>').join('')}q.oninput=page.onchange=render;if(category)category.onchange=render;render();</script></html>`;
}
const sectionPages = [
  ['ui.html', { title: 'UI testing · Smoke, Regression, Integration, Negative', suite: 'ui', rows: ui, extras: `<aside>Exactly 100 cases per type: Smoke 100 · Regression 100 · Integration 100 · Negative 100. Each case links to its page-specific locator map.</aside>` }],
  ['api.html', { title: 'API testing · requests and contracts', suite: 'api', rows: api, extras: `<aside>Each record lists method, full Nexora API path, auth/tenant headers, optional body, expected response and sanitized request-log fields. <a href="/catalog/api-requests.http">Download the 200-request HTTP collection</a>.</aside>` }],
  ['bdd.html', { title: 'BDD Cucumber · Gherkin scenarios', suite: 'bdd', rows: bdd, extras: `<aside>200 Given/When/Then scenarios in 48 page-level feature files. <a href="/catalog/bdd-features/">Browse all .feature files</a>.</aside>` }],
  ['database.html', { title: 'DB testing · data, actions and tenant context', suite: 'database', rows: db, extras: `<aside>1,000 database case records specify the backing table, fixture values, tenant A/B context, action, expected outcome, rollback/cleanup and safe DB logging.</aside>` }],
];
for (const [filename, options] of sectionPages) await writeFile(resolve(sectionDir, filename), sectionPage(options));
await writeFile(resolve(sectionDir, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · QA sections</title><style>${sectionStyles}</style><header><b>Nexora One · QA</b><a href="/">Report home</a><a href="/catalog/">All 1,800 cases</a></header><main class="wrap"><h1>Test sections</h1><p>Cases are grouped separately by test type and mapped to 48 Nexora screens.</p><p>${sectionNav}</p></main></html>`);
await writeFile(resolve(bddFeatureDir, 'index.html'), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nexora One · Cucumber features</title><style>${sectionStyles}</style><header><b>Nexora One · BDD Cucumber</b><a href="/catalog/sections/bdd.html">BDD case section</a><a href="/catalog/">All cases</a></header><main class="wrap"><h1>48 page-level feature files</h1><ul>${screens.map((s)=>`<li><a href="${encodeURIComponent(`${s.key}.feature`)}">${s.title} · ${s.section}</a></li>`).join('')}</ul></main></html>`);
console.log(`Wrote ${ui.length} UI, ${api.length} API, ${bdd.length} BDD, ${db.length} DB cases and ${screens.length} page locator maps.`);
