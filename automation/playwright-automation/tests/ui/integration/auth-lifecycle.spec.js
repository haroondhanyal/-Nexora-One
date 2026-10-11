import { test, expect } from '@playwright/test';
import { screenPageFor } from '../../../pages/index.js';

test.beforeEach(async ({ page }) => {
  await page.route('**/api-proxy/**', (route) => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: '{"detail":"API intentionally offline for local UI contract tests"}',
  }));
});

test('Authentication | loading state resolves to the local sign-in screen', async ({ page }) => {
  await page.goto('/', { waitUntil: 'commit' });
  const loading = screenPageFor(page, 'auth_loading');
  await expect(loading.locator('progress')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Sign in to Nexora One' })).toBeVisible();
  await expect(screenPageFor(page, 'auth_sign_in').signInButton).toBeVisible();
});

test('Authentication | local password reset explains demo account behavior', async ({ page }) => {
  await page.goto('/');
  const signIn = screenPageFor(page, 'auth_sign_in');
  await expect(page.getByRole('heading', { name: 'Sign in to Nexora One' })).toBeVisible();

  const dialogMessage = page.waitForEvent('dialog').then(async (dialog) => {
    const message = dialog.message();
    await dialog.accept();
    return message;
  });
  await signIn.resetPasswordLink.click();
  expect(await dialogMessage).toContain('Local demo accounts do not use passwords');
});

test('Authentication | local signup starts workspace creation', async ({ page }) => {
  await page.goto('/');
  await screenPageFor(page, 'auth_sign_in').signUpButton.click();
  await expect(page.getByRole('heading', { name: 'Start with your business' })).toBeVisible();
  await expect(screenPageFor(page, 'workspace_setup').companyName).toBeVisible();
});

test('Workspace setup | validates required fields and completes the local fallback', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Continue as local owner' }).click();
  await expect(page.getByRole('main')).toBeVisible();
  await page.getByRole('button', { name: /^Workspace:/i }).click();
  await page.getByRole('button', { name: /add workspace/i }).click();

  const setup = screenPageFor(page, 'workspace_setup');
  await expect(setup.pageTitle).toHaveText('Start with your business');
  await expect(setup.industryOptions).toHaveCount(6);
  await setup.createWorkspaceButton.click();
  expect(await setup.companyName.evaluate((input) => input.validity.valueMissing)).toBe(true);

  await setup.companyName.fill('Nexora QA Workspace');
  await page.getByRole('radio', { name: /distribution/i }).click();
  await expect(page.getByRole('radio', { name: /distribution/i })).toHaveAttribute('aria-checked', 'true');
  await setup.createWorkspaceButton.click();
  await expect(page.getByRole('heading', { name: 'Business overview' })).toBeVisible();
  await expect(page.getByText('Offline demo workspace is ready with sample records.')).toBeVisible();
});
