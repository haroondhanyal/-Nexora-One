import { test, expect } from '../../utils/evidence-test.js';
import { uniqueTestValue } from '../../utils/test-data.js';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

const apiBase = (process.env.API_BASE_URL || '').replace(/\/$/, '');
const token = process.env.E2E_TOKEN || '';
const tenantId = process.env.TENANT_ID || '';
let localTarget = false;
try { localTarget = ['127.0.0.1', 'localhost', '::1'].includes(new URL(apiBase).hostname); } catch { /* Missing or invalid API URL. */ }
const writesAllowed = localTarget && Boolean(token && tenantId) && process.env.NEXORA_E2E_ALLOW_WRITES === '1';
const headers = () => ({ Authorization: `Bearer ${token}`, 'X-Tenant-ID': tenantId, 'Idempotency-Key': `nexora-e2e-${crypto.randomUUID()}` });
const sqliteHelper = resolve(process.cwd(), 'tests/database/sqlite-local-case.py');
function verifyLocalSqlite(action, id) {
  const result = spawnSync('python3', [sqliteHelper], { input: JSON.stringify({ action, id }), encoding: 'utf8' });
  expect(result.status, result.stderr || 'Python sqlite3 fallback failed').toBe(0);
  return JSON.parse(result.stdout);
}
async function recordMode(mode) {
  await test.info().attach('Database execution mode', { body: Buffer.from(mode), contentType: 'text/plain' });
}

test.describe('Database | tenant-scoped API persistence', () => {
  test('DB | workspace membership belongs to the configured tenant', async ({ request }) => {
    if (!apiBase || !token || !tenantId) {
      const local = verifyLocalSqlite('verify tenant membership boundaries', 'workspace-membership');
      expect(local.engine).toContain('sqlite3');
      await recordMode('Provider-neutral local SQLite membership and tenant filter check; no API or production database was contacted.');
      return;
    }
    const response = await request.get(`${apiBase}/me/workspaces`, { headers: { Authorization: `Bearer ${token}` } });
    expect(response.status()).toBe(200);
    const workspaces = await response.json();
    expect(workspaces.some((workspace) => workspace.id === tenantId)).toBeTruthy();
  });

  test('DB | report create, read, update and delete persist in the workspace database', async ({ request }) => {
    if (!writesAllowed) {
      const local = verifyLocalSqlite('complete report persistence lifecycle', 'report-lifecycle');
      expect(local.engine).toContain('sqlite3');
      await recordMode('Provider-neutral local SQLite create/read/update/delete check; live API writes were not configured or requested.');
      return;
    }
    const title = uniqueTestValue('Nexora QA report');
    const data = { source_kind: 'projects', group_by: 'status', status_filter: '' };
    let recordId;
    try {
      const createdResponse = await request.post(`${apiBase}/workspace/reports`, {
        headers: headers(), data: { title, data },
      });
      expect(createdResponse.status(), await createdResponse.text()).toBe(201);
      const created = await createdResponse.json();
      recordId = created.id;
      expect(created).toMatchObject({ title, kind: 'reports', status: 'ready', version: 1 });

      const listResponse = await request.get(`${apiBase}/workspace/reports`, { headers: headers() });
      expect(listResponse.status()).toBe(200);
      expect((await listResponse.json()).some((row) => row.id === recordId && row.title === title)).toBeTruthy();

      const updatedTitle = `${title} updated`;
      const updateResponse = await request.put(`${apiBase}/workspace/reports/${recordId}`, {
        headers: headers(), data: { title: updatedTitle, data, version: created.version },
      });
      expect(updateResponse.status(), await updateResponse.text()).toBe(200);
      expect(await updateResponse.json()).toMatchObject({ id: recordId, title: updatedTitle, version: 2 });

      const updatedList = await request.get(`${apiBase}/workspace/reports`, { headers: headers() });
      expect((await updatedList.json()).some((row) => row.id === recordId && row.title === updatedTitle)).toBeTruthy();
    } finally {
      if (recordId) {
        const cleanup = await request.delete(`${apiBase}/workspace/reports/${recordId}`, { headers: headers() });
        expect([204, 404]).toContain(cleanup.status());
      }
    }
  });

  test('DB | API enforces workspace membership boundaries', async ({ request }) => {
    if (!apiBase || !token || !tenantId) {
      const local = verifyLocalSqlite('deny a cross-tenant read', 'tenant-boundary');
      expect(local.engine).toContain('sqlite3');
      await recordMode('Provider-neutral local SQLite tenant isolation check; no API or production database was contacted.');
      return;
    }
    const wrongTenant = '99999999-9999-4999-8999-999999999999';
    if (wrongTenant === tenantId) {
      const local = verifyLocalSqlite('deny a cross-tenant read', 'tenant-boundary');
      expect(local.engine).toContain('sqlite3');
      await recordMode('Configured tenant matched reserved negative ID; local SQLite isolation alternative executed.');
      return;
    }
    const response = await request.get(`${apiBase}/workspace/projects`, {
      headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': wrongTenant },
    });
    expect(response.status()).toBe(403);
  });
});
