import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { expect } from '@playwright/test';

function navigationButtonName(label) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`^${escaped}(?:\\s+P\\d+)?$`);
}

export class ScreenPage {
  constructor(page, screenKey) {
    this.page = page;
    this.screenKey = screenKey;
    const locatorUrl = new URL(`../locators/${screenKey}.json`, import.meta.url);
    this.contract = JSON.parse(readFileSync(fileURLToPath(locatorUrl), 'utf8'));
  }

  locator(name) {
    if (name === 'pageHeading') return this.page.getByRole('heading', { level: 1 });
    if (name === 'pageTitle' && !this.contract.selectors.pageTitle) return this.page.getByRole('heading').first();
    if (name === 'sidebarItem') return this.page.getByRole('button', { name: navigationButtonName(this.contract.navigationLabel) });
    if (name === 'tableHeader') return this.page.getByRole('columnheader');
    if (name === 'table') return this.page.getByRole('table');
    if (name === 'tableRows') return this.page.locator('tbody').getByRole('row');
    if (name === 'primaryContent' && this.contract.expectedFirstColumn) return this.page.getByRole('table');
    if (name === 'globalSearch') return this.page.getByPlaceholder('Search records...');
    if (name === 'workspaceSwitcher') return this.page.getByRole('button', { name: /^Workspace:/i });
    if (name === 'signInButton') return this.page.getByRole('button', { name: /continue as local owner|sign in securely/i });
    if (name === 'resetPasswordLink') return this.page.getByRole('button', { name: 'Forgot password?' });
    if (name === 'signUpButton') return this.page.getByRole('button', { name: /sign up|create a demo workspace/i });
    if (name === 'retryButton') return this.page.getByRole('button', { name: 'Retry' });
    if (name === 'createWorkspaceButton') return this.page.getByRole('button', { name: 'Create workspace' });
    if (name === 'industryOptions') return this.page.getByRole('radio');
    if (name === 'companyName') return this.page.locator('#workspace-name');
    if (name === 'password') return this.page.locator('#password');
    if (name === 'visiblePassword') return this.page.locator('#password:visible');
    const selector = this.contract.selectors[name];
    if (!selector) throw new Error(`No ${name} locator configured for ${this.screenKey}`);
    if (typeof selector === 'object') {
      if (selector.type === 'role') return this.page.getByRole(selector.role, Object.fromEntries(['name', 'exact', 'level', 'includeHidden'].filter((key) => selector[key] !== undefined).map((key) => [key, selector[key]])));
      if (selector.type === 'label') return this.page.getByLabel(selector.value, { exact: selector.exact ?? false });
      if (selector.type === 'placeholder') return this.page.getByPlaceholder(selector.value, { exact: selector.exact ?? false });
      if (selector.type === 'text') return this.page.getByText(selector.value, { exact: selector.exact ?? false });
      if (selector.type === 'id') return this.page.locator(`#${selector.value}`);
      if (selector.type === 'css') return this.page.locator(selector.selector);
      throw new Error(`Unsupported locator type “${selector.type}” for ${this.screenKey}.${name}`);
    }
    return this.page.locator(selector);
  }

  get pageHeading() {
    if (this.contract.selectors.pageHeading) return this.page.getByRole('heading', { level: 1 });
    if (this.contract.selectors.pageTitle) return this.locator('pageTitle');
    throw new Error(`No page heading locator configured for ${this.screenKey}`);
  }
  get primaryContent() { return this.locator('primaryContent'); }
  get workspaceSwitcher() { return this.locator('workspaceSwitcher'); }
  get globalSearch() { return this.locator('globalSearch'); }
  get table() { return this.locator('table'); }
  get tableRows() { return this.locator('tableRows'); }
  get tableCells() { return this.page.getByRole('cell'); }
  get primaryAction() { return this.locator('primaryAction'); }
  get form() { return this.locator('form'); }
  get validation() { return this.locator('validation'); }

  async open() {
    if (this.contract.section !== 'Authentication' && this.contract.section !== 'Workspace setup') {
      const nav = this.locator('sidebarItem');
      await nav.click();
      await expect(this.page.getByRole('heading', { level: 1 })).toHaveText(this.contract.expectedHeading);
      return;
    }

    await this.page.goto('/');
    if (this.screenKey === 'auth_sign_in') {
      await expect(this.locator('signInButton')).toBeVisible();
    } else if (this.screenKey === 'auth_sign_up') {
      const signUp = this.page.getByRole('button', { name: 'Sign up' });
      if (!(await signUp.count())) throw new Error('The hosted Sign up screen requires a non-demo Nexora identity-provider configuration');
      await signUp.click();
    } else if (this.screenKey === 'auth_password_reset') {
      if (await this.page.locator('.setup-local-note').count()) throw new Error('The hosted password-reset screen is not available in local-demo mode');
      await this.page.getByRole('button', { name: 'Forgot password?' }).click();
    } else if (this.screenKey === 'workspace_setup') {
      await this.page.getByRole('button', { name: 'Continue as local owner' }).click();
      await expect(this.page.getByRole('main')).toBeVisible();
      await this.page.getByRole('button', { name: /^Workspace:/i }).click();
      await this.page.getByRole('button', { name: /add workspace/i }).click();
      await expect(this.locator('pageTitle')).toHaveText('Start with your business');
    } else if (this.screenKey === 'auth_loading') {
      await expect(this.locator('progress')).toBeVisible();
    } else {
      throw new Error(`Opening ${this.screenKey} requires the configured identity-provider state`);
    }
  }
}
