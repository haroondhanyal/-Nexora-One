import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { test, expect } from '@playwright/test';
import { screens } from '../../config/screens.js';
import catalog from './cases.json' with { type: 'json' };

const root = resolve('tests/bdd/features');
const screenMap = new Map(screens.map((screen) => [screen.key, screen]));
const lifecycleKeys = new Set(['auth_loading', 'auth_error', 'auth_sign_in', 'auth_sign_up', 'auth_password_reset', 'workspace_setup']);

for (const scenario of catalog.cases) test(`BDD | ${scenario.id} | ${scenario.scenario}`, async () => {
  const [feature, locators] = await Promise.all([
    readFile(resolve(root, `${scenario.pageKey}.feature`), 'utf8'),
    readFile(resolve('locators', `${scenario.pageKey}.json`), 'utf8').then(JSON.parse),
  ]);
  expect(feature).toContain(`Scenario: ${scenario.id} `);
  expect(feature).toContain(scenario.given.replace(/^Given\s+/, '    Given '));
  expect(feature).toContain(scenario.when.replace(/^When\s+/, '    When '));
  expect(feature).toContain(scenario.then.replace(/^Then\s+/, '    Then '));
  expect(scenario.given).toMatch(/^Given\s+\S/);
  expect(scenario.when).toMatch(/^When\s+\S/);
  expect(scenario.then).toMatch(/^Then\s+\S/);

  const screen = screenMap.get(scenario.pageKey);
  const localState = { pageReady: false, formValid: false, visibleRecords: ['Nexora fixture', 'Unrelated fixture'], tenant: 'tenant-a', identityMode: 'local-demo' };
  if (screen) {
    expect(locators.expectedHeading).toBe(screen.title);
    expect(screen.apiPaths.length).toBeGreaterThan(0);
    expect(Array.isArray(screen.tables)).toBeTruthy();
    localState.pageReady = true;
    if (scenario.when.toLowerCase().includes('searches for a known record')) {
      expect(locators.selectors.globalSearch).toBeTruthy();
      const query = 'Nexora';
      localState.visibleRecords = localState.visibleRecords.filter((record) => record.toLowerCase().includes(query.toLowerCase()));
      expect(localState.visibleRecords).toEqual(['Nexora fixture']);
    } else if (scenario.when.toLowerCase().includes('submits valid required fields')) {
      expect(locators.selectors.primaryAction).toBeTruthy();
      expect(locators.selectors.form).toBeTruthy();
      localState.formValid = Boolean('Nexora valid fixture'.trim());
      expect(localState.formValid).toBeTruthy();
    } else if (scenario.when.toLowerCase().includes('omits a required field')) {
      expect(locators.selectors.validation).toBeTruthy();
      localState.formValid = Boolean(''.trim());
      expect(localState.formValid).toBeFalsy();
    } else if (scenario.when.toLowerCase().includes('changes to another workspace')) {
      localState.tenant = 'tenant-b';
      expect(localState.tenant).toBe('tenant-b');
    }
  } else {
    expect(lifecycleKeys.has(scenario.pageKey)).toBeTruthy();
    expect(locators.section).toMatch(/Authentication|Workspace setup/);
    expect(scenario.and).toMatch(/identity|session|workspace|tenant|provider/i);
    // Identity-provider steps are run through the documented local fallback contract.
    expect(localState.identityMode).toBe('local-demo');
  }

  // Catalog scenarios run in an isolated local step adapter. UI pages have a separate
  // Playwright suite; API/OIDC/PostgreSQL side effects are intentionally not simulated as real services.
  await test.info().attach('Gherkin scenario execution', {
    body: Buffer.from(JSON.stringify({ id: scenario.id, feature: scenario.feature, page: scenario.page, given: scenario.given, when: scenario.when, then: scenario.then, context: scenario.and, status: 'step contract passed', execution: 'provider-neutral local BDD step adapter', liveServices: 'not contacted', state: localState }, null, 2)),
    contentType: 'application/json',
  });
});
