import { test, expect } from '@playwright/test';
import { readdir, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

test('all page locator maps use valid Playwright CSS selectors', async ({ page }) => {
  const folder = resolve(process.cwd(), 'locators');
  const files = (await readdir(folder)).filter((file) => file.endsWith('.json'));
  expect(files).toHaveLength(48);

  for (const file of files) {
    const contract = JSON.parse(await readFile(resolve(folder, file), 'utf8'));
    expect(Object.keys(contract.selectors).length, file).toBeGreaterThan(0);
    for (const [name, selector] of Object.entries(contract.selectors)) {
      if (typeof selector === 'string') {
        expect(selector, `${file} → ${name}`).not.toMatch(/^(?:\/\/|\.\/)/);
        await page.locator(selector).count();
        continue;
      }
      expect(['role', 'label', 'placeholder', 'text', 'id', 'css'], `${file} → ${name}`).toContain(selector.type);
      if (selector.type === 'role') await page.getByRole(selector.role, { name: selector.name, exact: selector.exact, level: selector.level }).count();
      if (selector.type === 'label') await page.getByLabel(selector.value, { exact: selector.exact }).count();
      if (selector.type === 'placeholder') await page.getByPlaceholder(selector.value, { exact: selector.exact }).count();
      if (selector.type === 'text') await page.getByText(selector.value, { exact: selector.exact }).count();
      if (selector.type === 'id') await page.locator(`#${selector.value}`).count();
      if (selector.type === 'css') await page.locator(selector.selector).count();
    }
  }
});
