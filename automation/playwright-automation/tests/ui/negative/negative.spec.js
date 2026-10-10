import { test, expect } from '@playwright/test';
import { screenPageFor } from '../../../pages/index.js';
import { startLocalDemo } from '../../../utils/auth.js';
import { fakeProject } from '../../../utils/test-data.js';

test('Projects | empty required fields are rejected before save', async ({ page }) => {
  const project = screenPageFor(page, 'projects');
  await startLocalDemo(page);
  await project.open();
  await project.primaryAction.click();

  const form = project.form;
  await expect(form).toBeVisible();
  const sample = fakeProject();
  const requiredFields = form.locator('[required]');
  const requiredCount = await requiredFields.count();
  expect(requiredCount).toBeGreaterThan(1);
  await requiredFields.first().fill(sample.name);
  const requiredField = requiredFields.nth(1);
  await expect(requiredField).toBeVisible();
  expect(await requiredField.evaluate((field) => field.checkValidity())).toBe(false);
  await expect(form.locator('button[type="submit"]')).toBeVisible();
});
