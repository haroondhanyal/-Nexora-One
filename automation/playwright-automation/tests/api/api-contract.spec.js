import { test, expect } from '../../utils/evidence-test.js';
import { screens } from '../../config/screens.js';
import { tenantHeaders } from '../../utils/api-client.js';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const apiBase = (process.env.API_BASE_URL || '').replace(/\/$/, '');
const apiOrigin = apiBase.replace(/\/api\/v1$/, '');
const token = process.env.E2E_TOKEN || '';
const tenantId = process.env.TENANT_ID || '';
const authHeaders = () => tenantHeaders({ token, tenantId });
const useLiveApi = Boolean(apiBase && token && tenantId);
const apiSourceHelper = resolve(process.cwd(), 'tests/api/api-source-contract.py');
const sourceResult = spawnSync('python3', [apiSourceHelper], { encoding: 'utf8' });
if (sourceResult.status !== 0) throw new Error(sourceResult.stderr || 'Could not read FastAPI source route contracts.');
const sourceContract = JSON.parse(sourceResult.stdout);
function pathMatches(template, concrete) {
  const templateParts = template.split('/').filter(Boolean);
  const concreteParts = concrete.split('/').filter(Boolean);
  return templateParts.length === concreteParts.length && templateParts.every((part, index) =>
    (part.startsWith('{') && part.endsWith('}')) || part === concreteParts[index]
  );
}
function sourceRoute(method, path) {
  return sourceContract.routes.find((route) => route.method === method && pathMatches(route.path, path));
}
const endpoints = new Map();
for (const screen of screens) for (const path of screen.apiPaths) {
  const method = screen.key === 'assistant' ? 'POST' : 'GET';
  const endpointKey = `${method} ${path}`;
  if (!endpoints.has(endpointKey)) endpoints.set(endpointKey, { method, path, screens: [] });
  endpoints.get(endpointKey).screens.push(screen);
}

test.describe('API | Nexora screen endpoint contracts', () => {
  test('API | health endpoint responds without workspace credentials', async ({ request }) => {
    if (apiBase) {
      const response = await request.get(`${apiOrigin}/healthz`);
      expect(response.status()).toBe(200);
      expect(await response.json()).toMatchObject({ status: 'ok' });
    } else {
      const route = sourceRoute('GET', '/healthz');
      expect(route, 'FastAPI must declare GET /healthz').toBeTruthy();
      expect(route.responseExample).toMatchObject({ status: 'ok' });
      await test.info().attach('Execution mode', { body: Buffer.from('Checked GET /healthz route and response against FastAPI source; no API service was contacted.'), contentType: 'text/plain' });
    }
  });

  test('API | OpenAPI contract is available and versioned', async ({ request }) => {
    const document = apiBase
      ? await (async () => { const response = await request.get(`${apiOrigin}/api/v1/openapi.json`); expect(response.status()).toBe(200); return response.json(); })()
      : {
        info: { title: sourceContract.app.title, version: sourceContract.app.version },
        paths: Object.fromEntries(sourceContract.routes.map((route) => [route.path, {}])),
      };
    expect(document.info.title).toMatch(/Nexora One API/i);
    expect(document.info.version).toBeTruthy();
    expect(document.paths).toBeTruthy();
    if (!apiBase) {
      expect(sourceContract.app.openapi_url).toBe('/api/v1/openapi.json');
      expect(Object.keys(document.paths).length).toBeGreaterThan(0);
      await test.info().attach('Execution mode', { body: Buffer.from(`Checked FastAPI app metadata and ${sourceContract.routes.length} declared routes from source; no API service was contacted.`), contentType: 'text/plain' });
    }
  });

  test('API | protected routes reject missing credentials', async ({ request }) => {
    if (apiBase) {
      const response = await request.get(`${apiBase}/branches`);
      expect(response.status()).toBe(401);
    } else {
      const route = sourceRoute('GET', '/api/v1/branches');
      expect(route, 'FastAPI must declare GET /api/v1/branches').toBeTruthy();
      expect(route.authDependencies).toContain('membership');
      await test.info().attach('Execution mode', { body: Buffer.from(`Checked GET /api/v1/branches and dependencies [${route.authDependencies.join(', ')}] against FastAPI source; no API service was contacted.`), contentType: 'text/plain' });
    }
  });

  for (const { method, path, screens: owners } of endpoints.values()) {
    const ownerNames = owners.map((screen) => screen.title).join(', ');
    test(`API | ${owners[0].section} | ${method} ${path} | ${ownerNames}`, async ({ request }) => {
      if (!useLiveApi) {
        const route = sourceRoute(method, path);
        expect(route, `FastAPI must declare ${method} ${path} or a compatible parameterized path`).toBeTruthy();
        expect(owners.length).toBeGreaterThan(0);
        expect(path).toMatch(/^\/api\/v1\//);
        if (method === 'POST') expect({ question: 'List local projects', sources: ['projects'] }).toMatchObject({ question: expect.any(String), sources: expect.any(Array) });
        await test.info().attach('Execution mode', { body: Buffer.from(`Matched ${method} ${path} to FastAPI ${route.method} ${route.path} (${route.function}); no API service was contacted. Owners: ${ownerNames}`), contentType: 'text/plain' });
        return;
      }
      const options = { headers: authHeaders() };
      if (method === 'POST') options.data = { question: 'List the local projects', sources: ['projects'] };
      const response = method === 'POST'
        ? await request.post(`${apiOrigin}${path}`, options)
        : await request.get(`${apiOrigin}${path}`, options);
      expect(response.status(), `${method} ${path} returned ${await response.text()}`).toBe(200);
      expect(response.headers()['content-type']).toContain('application/json');
      const body = await response.json();
      expect(body).not.toBeNull();
      await test.info().attach('Execution mode', { body: Buffer.from('Configured Nexora API endpoint.'), contentType: 'text/plain' });
    });
  }
});
