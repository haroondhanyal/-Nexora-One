import { spawnSync } from 'node:child_process';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { cases } from './case-catalog.js';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)));
const output = resolve(root, 'report-output');
await mkdir(output, { recursive: true });
await Promise.all(['native-k6-summary.json', 'k6-metrics.ndjson'].map((name) => writeFile(resolve(output, name), '')));

async function loadEnv(file) {
  try {
    const source = await readFile(file, 'utf8');
    for (const line of source.split(/\r?\n/)) {
      const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
      if (match && !process.env[match[1]]) process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
    }
  } catch { /* Environment variables can be supplied by VS Code or CI. */ }
}
await loadEnv(resolve(root, '../../../.env'));
await loadEnv(resolve(root, '../../.env'));
await loadEnv(resolve(root, '../../playwright-automation/.env'));

const apiBase = process.env.API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
const summaryPath = resolve(output, 'native-k6-summary.json');
const metricsPath = resolve(output, 'k6-metrics.ndjson');
const start = new Date().toISOString();
const version = spawnSync('k6', ['version'], { encoding: 'utf8' });
const missing = ['E2E_TOKEN', 'TENANT_ID'].filter((key) => !process.env[key]);
let status = 'not_run';
let exitCode = null;
let cli = '';

if (missing.length) {
  cli = `K6 workload not started. Configure ${missing.join(' and ')} for a disposable Nexora test workspace.`;
  console.error(cli);
} else if (version.error) {
  cli = `K6 workload not started: ${version.error.message}`;
  console.error(cli);
} else {
  const run = spawnSync('k6', ['run', '--out', `json=${metricsPath}`, 'performance-cases.js'], {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 30 * 1024 * 1024,
    env: { ...process.env, API_BASE_URL: apiBase, K6_SUMMARY_PATH: summaryPath },
  });
  cli = `${run.stdout || ''}${run.stderr || ''}`;
  exitCode = run.status ?? 1;
  status = exitCode === 0 ? 'completed' : 'failed';
  if (run.error) cli = `K6 failed to start: ${run.error.message}\n${cli}`;
  process.stdout.write(cli);
}

await writeFile(resolve(output, 'k6-cli-output.txt'), cli);
await writeFile(resolve(output, 'run-meta.json'), JSON.stringify({
  product: 'Nexora One', framework: 'k6', suite: 'full-route workspace API', status,
  apiBaseUrl: new URL(apiBase).origin + new URL(apiBase).pathname.replace(/\/$/, ''),
  k6Version: `${version.stdout || ''}${version.stderr || ''}`.trim(), configuredVUs: Number(process.env.K6_VUS || 8),
  expectedCases: cases.length, startedAt: start, finishedAt: new Date().toISOString(), exitCode,
  missingConfiguration: missing,
}, null, 2));

const report = spawnSync(process.execPath, ['render-report.mjs'], { cwd: root, encoding: 'utf8', maxBuffer: 5 * 1024 * 1024 });
if (report.stdout) process.stdout.write(report.stdout);
if (report.stderr) process.stderr.write(report.stderr);
if (report.status !== 0) process.exitCode = report.status || 1;
else if (exitCode !== 0) process.exitCode = exitCode ?? 2;
