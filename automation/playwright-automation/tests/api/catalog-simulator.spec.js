import { createServer } from 'node:http';
import { test, expect } from '../../utils/evidence-test.js';
import { screens } from '../../config/screens.js';
import catalog from './cases.json' with { type: 'json' };

const knownRoutes = new Map();
for (const screen of screens) for (const path of screen.apiPaths) {
  const method = screen.key === 'assistant' ? 'POST' : 'GET';
  knownRoutes.set(`${method} ${path}`, screen.title);
}
let server;
let localBase;

test.describe('API | Provider-neutral local contract simulator', () => {
  test.beforeAll(async () => {
    server = createServer(async (request, response) => {
      const url = new URL(request.url, 'http://127.0.0.1');
      const routeTitle = knownRoutes.get(`${request.method} ${url.pathname}`);
      const bearer = request.headers.authorization;
      const tenant = request.headers['x-tenant-id'];
      let status = 200;
      let body = { items: [], tenant_id: tenant || null, route: routeTitle || null };
      if (!routeTitle) { status = 404; body = { detail: 'Unknown route in local screen contract.' }; }
      else if (!bearer) { status = 401; body = { detail: 'Authentication required.' }; }
      else if (!tenant) { status = 400; body = { detail: 'X-Tenant-ID is required.' }; }
      else if (tenant === 'foreign-test-tenant') { status = 403; body = { detail: 'Tenant access denied.' }; }
      response.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
      response.end(JSON.stringify(body));
    });
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    localBase = `http://127.0.0.1:${server.address().port}`;
  });
  test.afterAll(async () => { if (server?.listening) await new Promise((resolve) => server.close(resolve)); });

  for (const scenario of catalog.cases) test(`API | ${scenario.id} | ${scenario.title}`, async () => {
    const kind = scenario.title.split(' · ')[0];
    const headers = { Accept: 'application/json' };
    if (kind !== 'missing-auth') headers.Authorization = 'Bearer local-simulator-token';
    if (kind !== 'missing-tenant') headers['X-Tenant-ID'] = kind === 'wrong-tenant' ? 'foreign-test-tenant' : 'local-test-tenant';
    const response = await fetch(`${localBase}${scenario.path}`, {
      method: scenario.method,
      headers,
      ...(scenario.body ? { body: JSON.stringify(scenario.body), headers: { ...headers, 'content-type': 'application/json' } } : {}),
    });
    const responseBody = await response.json();
    const expectedStatus = kind === 'missing-auth' ? 401 : kind === 'missing-tenant' ? 400 : kind === 'wrong-tenant' ? 403 : 200;
    expect(response.status, `${scenario.id}: ${scenario.method} ${scenario.path}`).toBe(expectedStatus);
    expect(response.headers.get('content-type')).toContain('application/json');
    if (expectedStatus === 200) expect(responseBody.tenant_id).toBe('local-test-tenant');
    else expect(JSON.stringify(responseBody)).not.toContain('items');
    await test.info().attach('Local API contract case', {
      body: Buffer.from(JSON.stringify({ id: scenario.id, mode: 'local route/auth/tenant simulator; no Nexora API service was contacted', method: scenario.method, path: scenario.path, expectedStatus, actualStatus: response.status, expected: scenario.expected, response: responseBody }, null, 2)),
      contentType: 'application/json',
    });
  });
});
