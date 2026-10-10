import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('../', import.meta.url)));
const executable = resolve(root, 'node_modules/.bin', process.platform === 'win32' ? 'playwright.cmd' : 'playwright');
const port = Number(process.env.REPORT_PORT || 4178);
const base = process.env.REPORT_BASE_URL || `http://127.0.0.1:${port}`;
let server;

async function isReportAvailable() {
  try { return (await fetch(base, { signal: AbortSignal.timeout(1000) })).ok; }
  catch { return false; }
}

async function waitForReport(child) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (await isReportAvailable()) return true;
    if (child.exitCode !== null) return false;
    await new Promise((resolveWait) => setTimeout(resolveWait, 250));
  }
  return false;
}

if (!(await isReportAvailable())) {
  server = spawn(process.execPath, ['scripts/serve-report.mjs'], {
    cwd: root,
    env: { ...process.env, REPORT_PORT: String(port) },
    stdio: 'ignore',
  });
  if (!(await waitForReport(server))) {
    console.error('Could not start the report server for screenshot capture.');
    server.kill();
    process.exit(1);
  }
}

const result = spawn(executable, ['test', 'tests/report-screenshots.spec.js', '--workers=1'], {
  cwd: root,
  env: { ...process.env, REPORT_BASE_URL: base, REPORT_CAPTURE: '1' },
  stdio: 'inherit',
});
result.on('error', (error) => {
  console.error(`Could not start report screenshot capture: ${error.message}`);
  process.exitCode = 1;
});
result.on('exit', (code) => {
  process.exitCode = code ?? 1;
  if (server && server.exitCode === null) server.kill();
});
