import { expect } from '@playwright/test';

export async function startLocalDemo(page, { width, height, openMobileMenu = false } = {}) {
  if (width && height) await page.setViewportSize({ width, height });
  await page.route('**/api-proxy/**', (route) => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: '{"detail":"API intentionally offline for local UI contract tests"}',
  }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Continue as local owner' }).click();
  await expect(page.getByRole('main')).toBeVisible();
  if (openMobileMenu && width <= 900) await page.getByRole('button', { name: 'Open menu' }).click();
}
