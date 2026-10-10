import { config } from 'dotenv';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectDir = resolve(dirname(fileURLToPath(import.meta.url)), '..');

// Package-local values take precedence; existing shell variables always win.
export function loadTestEnvironment() {
  for (const file of [
    resolve(projectDir, '.env'),
    resolve(projectDir, '../.env'),
    resolve(projectDir, '../../.env'),
  ]) config({ path: file, override: false });
}

export function envValue(name, fallback = '') {
  return process.env[name] || fallback;
}

export function hasApiTestConfiguration() {
  return Boolean(envValue('API_BASE_URL') && envValue('E2E_TOKEN') && envValue('TENANT_ID'));
}
