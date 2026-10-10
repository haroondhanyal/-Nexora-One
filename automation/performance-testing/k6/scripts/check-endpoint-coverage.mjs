import { execFileSync } from 'node:child_process';
import { endpointOperations, screenEndpointReads } from '../case-catalog.js';
import { screenContracts } from '../../../playwright-automation/config/screen-contracts.js';

import { fileURLToPath } from 'node:url';
const routeFile = fileURLToPath(new URL('./list-api-routes.py', import.meta.url));
const sourceRoutes = JSON.parse(execFileSync('python3', [routeFile], { encoding: 'utf8' }));
const k6Routes = new Set(endpointOperations.map(({ method, path }) => `${method} ${path}`));
const sourceKeys = new Set(sourceRoutes.map(({ method, path }) => `${method} ${path}`));
const missing = [...sourceKeys].filter((route) => !k6Routes.has(route));
const stale = [...k6Routes].filter((route) => !sourceKeys.has(route));
const screenPaths = new Set([
  ...screenEndpointReads.map(([path]) => `/api/v1${path}`),
  ...endpointOperations.map(({ path }) => path),
]);
const missingScreenPaths = Object.values(screenContracts).flatMap((screen) => screen.apiPaths
  .filter((path) => ![...screenPaths].some((candidate) => {
    const pattern = candidate.split('/').map((segment) => /^\{.+\}$/.test(segment) ? '[^/]+' : segment).join('/');
    return new RegExp(`^${pattern}$`).test(path);
  }))
  .map((path) => `${screen.key}: ${path}`));

if (missing.length || stale.length || missingScreenPaths.length) {
  if (missing.length) console.error(`Missing from K6 inventory:\n${missing.map((route) => `  ${route}`).join('\n')}`);
  if (stale.length) console.error(`No longer present in FastAPI:\n${stale.map((route) => `  ${route}`).join('\n')}`);
  if (missingScreenPaths.length) console.error(`Nexora screen API paths missing from K6:\n${missingScreenPaths.map((route) => `  ${route}`).join('\n')}`);
  process.exitCode = 1;
} else {
  console.log(`K6 coverage verified: all ${sourceKeys.size} FastAPI method/path routes and all ${Object.keys(screenContracts).length} screen API mappings are catalogued.`);
}
