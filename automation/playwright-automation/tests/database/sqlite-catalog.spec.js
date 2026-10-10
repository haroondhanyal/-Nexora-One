import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { test, expect } from '@playwright/test';
import catalog from './cases.json' with { type: 'json' };

const sqliteRunner = resolve('tests/database/sqlite-local-case.py');
const casesToExecute = catalog.cases.slice(0, 150);

test.describe('Database | Local SQLite provider-neutral cases', () => {
  for (const scenario of casesToExecute) test(`DB | ${scenario.id} | ${scenario.table} | ${scenario.action}`, async () => {
    const result = execFileSync('python3', [sqliteRunner], { input: JSON.stringify(scenario), encoding: 'utf8', timeout: 10_000 });
    const evidence = JSON.parse(result);
    expect(evidence.case).toBe(scenario.id);
    expect(evidence.engine).toContain('sqlite3 in-memory');
    await test.info().attach('Local database execution context', {
      body: Buffer.from(JSON.stringify({ ...evidence, tableContract: scenario.table, expected: scenario.expected, actualPostcondition: 'SQLite assertion completed; database discarded after this test', notVerified: 'PostgreSQL schema, migrations, RLS, and Nexora service persistence' }, null, 2)),
      contentType: 'application/json',
    });
  });
});
