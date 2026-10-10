import { test, expect } from '@playwright/test';
import { screens } from '../../../config/screens.js';
import { screenPageFor } from '../../../pages/index.js';
import { startLocalDemo } from '../../../utils/auth.js';

async function signInDemo(page) {
  await startLocalDemo(page);
}

for (const screen of screens) {
  test.describe(`UI | ${screen.section} | ${screen.title} page object`, () => {
      test(`${screen.title} | ${screen.key} page locator and data contract`, async ({ page }) => {
        await page.setViewportSize({ width: 1440, height: 960 });
        await signInDemo(page);
        const screenPage = screenPageFor(page, screen.key);
        await screenPage.open();
        await expect(screenPage.pageHeading).toHaveText(screen.title);
        await expect(screenPage.sidebarItem).toHaveClass(/active/);
        await expect(screenPage.primaryContent).toBeVisible();
        await expect(screenPage.workspaceSwitcher).toBeVisible();
        await expect(screenPage.globalSearch).toBeVisible();
        if (screen.primaryHeader) {
          await expect(screenPage.table).toBeVisible();
          await expect(screenPage.table.locator('thead th').first()).toHaveText(screen.primaryHeader);
        }
        expect(screen.apiPaths.length, `${screen.title} should map to at least one API path`).toBeGreaterThan(0);
        expect(screen.dataSource, `${screen.title} should document its backing data source`).toBeTruthy();
      });
  });
}
