import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const base = process.env.REPORT_BASE_URL || 'http://127.0.0.1:4178';
const reports = [
  ['nexora-qa-center', '/', /Nexora One.*Automation/i],
  ['nexora-allure-report', '/allure/index.html', /Allure/i],
  ['nexora-k6-analytics', '/performance/index.html', /K6 Performance Report/i],
  ['nexora-k6-native-report', '/performance/native-k6-report.html', /Native K6 Summary/i],
];

for (const [name, path, title] of reports) test(`automation evidence · ${name}`, async ({ page }) => {
  await page.goto(`${base}${path}`);
  await expect(page).toHaveTitle(title);
  await expect(page.locator('body')).toBeVisible();
  if (path === '/allure/index.html') await page.locator('#content .side-nav__link').first().waitFor({ state: 'visible' });
  const folder = resolve(process.cwd(), 'screenshots/report');
  await mkdir(folder, { recursive: true });
  await page.screenshot({ path: resolve(folder, `${name}.png`), fullPage: true, animations: 'disabled' });
  await test.info().attach(`${name}-report-screenshot`, { path: resolve(folder, `${name}.png`), contentType: 'image/png' });
});

test('automation evidence · nexora-allure-categories', async ({ page }) => {
  await page.goto(`${base}/allure/index.html`);
  const item = page.locator('#content .side-nav__link').filter({ hasText: 'Categories' });
  await item.waitFor({ state: 'visible' });
  await item.click({ noWaitAfter: true });
  await expect(page.locator('#content .side-nav__link_active')).toContainText(/Categories/i);
  const folder = resolve(process.cwd(), 'screenshots/report');
  await mkdir(folder, { recursive: true });
  const image = resolve(folder, 'nexora-allure-categories.png');
  await page.screenshot({ path: image, fullPage: true, animations: 'disabled' });
  await test.info().attach('nexora-allure-categories-screenshot', { path: image, contentType: 'image/png' });
});

const allureSections = ['Suites', 'Behaviors', 'Packages', 'Graphs', 'Timeline'];
for (const section of allureSections) test(`automation evidence · nexora-allure-${section.toLowerCase()}`, async ({ page }) => {
  await page.goto(`${base}/allure/index.html`);
  const item = page.locator('#content .side-nav__link').filter({ hasText: section });
  await item.waitFor({ state: 'visible' });
  await item.click({ noWaitAfter: true });
  await expect(page.locator('#content .side-nav__link_active')).toContainText(new RegExp(section, 'i'));
  const folder = resolve(process.cwd(), 'screenshots/report');
  await mkdir(folder, { recursive: true });
  const image = resolve(folder, `nexora-allure-${section.toLowerCase()}.png`);
  await page.screenshot({ path: image, fullPage: section === 'Graphs', animations: 'disabled' });
  await test.info().attach(`nexora-allure-${section.toLowerCase()}-screenshot`, { path: image, contentType: 'image/png' });
});
