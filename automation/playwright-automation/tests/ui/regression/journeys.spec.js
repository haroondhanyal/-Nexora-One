import { test, expect } from '@playwright/test';
import { startLocalDemo } from '../../../utils/auth.js';

const viewports = [
  ['wide desktop', 1440, 900], ['desktop', 1280, 800], ['laptop', 1024, 768],
  ['tablet', 768, 1024], ['mobile', 390, 844], ['small mobile', 360, 740],
];

async function enterWorkspace(page, width) {
  const height = width < 500 ? 844 : 850;
  await startLocalDemo(page, { width, height, openMobileMenu: true });
}

const flows = [
  ['workspace selector lists ten sample companies', async (page) => {
    await page.getByRole('button', { name: /^Workspace:/i }).click();
    await expect(page.locator('.workspace-option')).toHaveCount(11);
    await expect(page.getByRole('button', { name: /Crescent Retail Group.*Retail & commerce/ })).toBeVisible();
  }],
  ['switching sample companies updates the Nexora workspace', async (page) => {
    await page.getByRole('button', { name: /^Workspace:/i }).click();
    await page.getByRole('button', { name: /Northstar Foods/ }).click();
    await expect(page.getByRole('button', { name: /^Workspace: Northstar Foods$/ })).toBeVisible();
    await expect(page.locator('.page-footer')).toContainText('Illustrative sample · read only');
  }],
  ['Add workspace opens the company setup screen', async (page) => {
    await page.getByRole('button', { name: /^Workspace:/i }).click();
    await page.getByRole('button', { name: /add workspace/i }).click();
    await expect(page.getByRole('heading', { name: 'Start with your business' })).toBeVisible();
  }],
  ['sidebar navigation opens the Workflow designer', async (page) => {
    await page.getByRole('button', { name: 'Workflow designer' }).click();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Workflow designer');
  }],
  ['adding an operational record opens its edit form', async (page) => {
    await page.locator('aside.sidebar').getByRole('button', { name: /^Projects(?:\s+P\d+)?$/ }).click();
    await page.getByRole('button', { name: 'Add project' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Add project' })).toBeVisible();
  }],
  ['workspace search accepts and clears a query', async (page, width) => {
    const closeMenu = page.locator('aside.sidebar').getByRole('button', { name: 'Close menu' });
    if (await closeMenu.isVisible()) await closeMenu.click();
    const search = page.getByPlaceholder('Search records...');
    if (!(await search.isVisible())) await page.locator('.search-box').click();
    await search.fill('invoice');
    await expect(search).toHaveValue('invoice');
    await search.clear();
  }],
  ['appearance screen exposes Nexora themes', async (page) => {
    await page.getByRole('button', { name: 'Profile & settings' }).click();
    await expect(page.getByRole('heading', { name: 'Profile & settings' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Emerald Light' })).toBeVisible();
  }],
  ['profile control opens the sign-out confirmation', async (page) => {
    await page.getByRole('button', { name: /sign out/i }).click();
    await expect(page.getByRole('heading', { name: 'Sign out of this workspace?' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Stay signed in' })).toBeVisible();
  }],
  ['overview keeps the brand and workspace cards visible', async (page) => {
    await expect(page.getByRole('img', { name: 'Nexora One' })).toBeVisible();
    await expect(page.locator('.overview-metrics')).toBeVisible();
  }],
  ['mobile navigation can open and close', async (page, width) => {
    if (width > 900) {
      await expect(page.locator('aside.sidebar')).toBeVisible();
      return;
    }
    await page.getByRole('button', { name: 'Close menu' }).click();
    await page.getByRole('button', { name: 'Open menu' }).click();
    await expect(page.locator('aside.sidebar')).toHaveClass(/sidebar-open/);
  }],
];

for (const [title, run] of flows) for (const [viewport, width, height] of viewports) {
  test(`journey · ${title} · ${viewport}`, async ({ page }) => {
    await enterWorkspace(page, width);
    await page.setViewportSize({ width, height });
    await run(page, width);
  });
}
