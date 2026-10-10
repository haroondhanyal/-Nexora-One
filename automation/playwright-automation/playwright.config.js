import { defineConfig, devices } from '@playwright/test';
import { loadTestEnvironment } from './utils/env.js';

loadTestEnvironment();

export default defineConfig({
  testDir: './tests',
  testMatch: process.env.REPORT_CAPTURE ? ['report-screenshots.spec.js'] : ['**/*.spec.js'],
  testIgnore: process.env.REPORT_CAPTURE ? [] : ['**/report-screenshots.spec.js'],
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: Number(process.env.PW_WORKERS || 6),
  timeout: 90_000,
  expect: { timeout: 30_000 },
  reporter: process.env.REPORT_CAPTURE ? [['list']] : [
    ['list'],
    ['html', { outputFolder: './playwright-report', open: 'never' }],
    ['json', { outputFile: './report/playwright-results.json' }],
    ['allure-playwright', { resultsDir: './allure-results', detail: true, suiteTitle: true, environmentInfo: { product: 'Nexora One', testFramework: 'Playwright', testScope: '42 application screens' } }],
  ],
  outputDir: process.env.REPORT_CAPTURE ? './report-screenshot-test-results' : './test-results',
  use: { baseURL: process.env.WEB_BASE_URL || 'http://127.0.0.1:3000', trace: 'retain-on-failure', screenshot: 'on', video: 'on', ...devices['Desktop Chrome'] },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: process.env.REPORT_CAPTURE || process.env.WEB_BASE_URL ? undefined : {
    command: 'npm run dev -- --hostname 127.0.0.1',
    cwd: '../../apps/web',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: { NEXT_PUBLIC_LOCAL_DEMO: 'true' },
  },
});
