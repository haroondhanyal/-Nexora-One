import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { screens } from '../../../config/screens.js';
import { startLocalDemo } from '../../../utils/auth.js';
import { screenPageFor } from '../../../pages/index.js';

const viewports = [
  ['wide desktop', 1440, 900], ['desktop', 1280, 800], ['laptop', 1024, 768],
  ['tablet', 768, 1024], ['mobile', 390, 844], ['small mobile', 360, 740],
];

async function enterWorkspace(page) {
  const { width, height } = page.viewportSize();
  await startLocalDemo(page, { width, height, openMobileMenu: true });
}

async function openScreen(page, screen) {
  await enterWorkspace(page);
  const screenPage = screenPageFor(page, screen.key);
  await screenPage.sidebarItem.click();
  await expect(screenPage.pageHeading).toHaveText(screen.title);
}

for (const screen of screens) {
  test.describe(`Nexora UI · ${screen.title} · 20 cases`, () => {
    for (const [name, width, height] of viewports) test(`${screen.key} · renders at ${name} (${width}px)`, async ({ page }) => {
      await page.setViewportSize({ width, height });
      await openScreen(page, screen);
      await expect(page.getByRole('main')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 8);
    });

    test(`${screen.key} · exposes its page heading`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.getByRole('heading', { level: 1, name: screen.title })).toBeVisible();
    });
    test(`${screen.key} · uses the Nexora One browser title`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page).toHaveTitle(/Nexora One/i);
    });
    test(`${screen.key} · displays the Nexora One wordmark`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.getByRole('img', { name: 'Nexora One' })).toBeVisible();
    });
    test(`${screen.key} · marks its sidebar destination active`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(screenPageFor(page, screen.key).sidebarItem).toHaveClass(/active/);
    });
    test(`${screen.key} · exposes the workspace switcher`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.getByRole('button', { name: /^Workspace:/i })).toBeVisible();
    });
    test(`${screen.key} · exposes global record search`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.getByPlaceholder('Search records...')).toBeVisible();
    });
    test(`${screen.key} · provides a main landmark`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.getByRole('main')).toBeVisible();
    });
    test(`${screen.key} · keeps all page images loadable`, async ({ page }) => {
      await openScreen(page, screen);
      const images = page.getByRole('main').locator('img');
      await expect.poll(() => images.evaluateAll((items) => items.filter((img) => !img.complete || img.naturalWidth === 0).map((img) => img.getAttribute('src')))).toEqual([]);
    });
    test(`${screen.key} · keeps search usable`, async ({ page }) => {
      await openScreen(page, screen);
      const search = page.getByPlaceholder('Search records...');
      await search.fill('Nexora QA search');
      await expect(search).toHaveValue('Nexora QA search');
      await search.clear();
    });
    test(`${screen.key} · keeps the page inside its primary application shell`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.locator('.main-area')).toBeVisible();
      await expect(page.locator('.page-content')).toBeVisible();
    });
    test(`${screen.key} · provides keyboard focus visibility`, async ({ page }) => {
      await openScreen(page, screen);
      await page.keyboard.press('Tab');
      expect(await page.evaluate(() => document.activeElement !== document.body)).toBe(true);
    });
    test(`${screen.key} · gives its navigation item an accessible name`, async ({ page }) => {
      await openScreen(page, screen);
      const activeNavigation = page.locator('.nav-item.active');
      await expect(activeNavigation).not.toHaveAttribute('aria-label', '');
      await expect(activeNavigation).toContainText(screen.navTitle);
    });
    test(`${screen.key} · keeps the navigation groups available`, async ({ page }) => {
      await openScreen(page, screen);
      await expect(page.locator('.nav-group')).toHaveCount(8);
    });
    test(`${screen.key} · captures a separate Nexora screen image`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await openScreen(page, screen);
      const folder = resolve(process.cwd(), 'screenshots/runs');
      await mkdir(folder, { recursive: true });
      const path = resolve(folder, `${screen.key}.png`);
      await page.screenshot({ path, fullPage: true, animations: 'disabled' });
      await test.info().attach(`${screen.key}-screen`, { path, contentType: 'image/png' });
      await expect(screenPageFor(page, screen.key).pageHeading).toHaveText(screen.title);
    });
  });
}
