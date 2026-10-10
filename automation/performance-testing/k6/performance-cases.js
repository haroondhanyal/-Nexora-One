import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { Trend, Rate } from 'k6/metrics';
import { cases } from './case-catalog.js';

const caseLatency = new Trend('nexora_case_latency', true);
const caseFailures = new Rate('nexora_case_failures');
const apiBase = (__ENV.API_BASE_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '');
const apiOrigin = new URL(apiBase).origin;
const token = __ENV.E2E_TOKEN || '';
const tenantId = __ENV.TENANT_ID || '';
const sentinelId = 'ffffffff-ffff-ffff-ffff-ffffffffffff';
const configuredIds = (() => {
  try { return JSON.parse(__ENV.K6_RESOURCE_IDS || '{}'); } catch { return {}; }
})();

const workloadProfiles = {
  steady: { vus: 1, startTime: '0s' },
  repeat: { vus: 2, startTime: '15s' },
  burst: { vus: Number(__ENV.K6_VUS || 8), startTime: '30s' },
  recovery: { vus: 1, startTime: '45s' },
  consistency: { vus: 2, startTime: '60s' },
  'safe-validation': { vus: 1, startTime: '75s' },
};
const casesByProfile = Object.fromEntries(Object.keys(workloadProfiles).map((profile) => [
  profile,
  cases.filter((testCase) => testCase.profile === profile),
]));

export const options = {
  scenarios: Object.fromEntries(Object.entries(workloadProfiles).map(([profile, settings]) => [
    `nexora_${profile.replaceAll('-', '_')}`,
    {
      executor: 'shared-iterations',
      exec: 'runCase',
      startTime: settings.startTime,
      vus: settings.vus,
      iterations: casesByProfile[profile].length,
      maxDuration: __ENV.K6_MAX_DURATION || '4m',
      tags: { profile },
    },
  ])),
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<1200', 'p(99)<2500'],
    nexora_case_failures: ['rate<0.02'],
  },
};

function targetUrl(testCase) {
  const path = testCase.path.replace(/\{([^}]+)\}/g, (_, key) => {
    const catalogValue = testCase.params?.[key];
    return catalogValue && catalogValue !== '__K6_RESOURCE_ID__' ? catalogValue : configuredIds[key] || sentinelId;
  });
  if (testCase.root) return `${apiOrigin}${path}`;
  return `${apiBase}${path.replace(/^\/api\/v1/, '')}`;
}

export function runCase() {
  const profile = exec.scenario.name.replace(/^nexora_/, '').replaceAll('_', '-');
  const testCase = casesByProfile[profile][exec.scenario.iterationInTest];
  const tags = {
    case_id: testCase.id,
    screen: testCase.screen,
    method: testCase.method,
    profile: testCase.profile,
    endpoint: testCase.path,
  };
  const headers = {
    Authorization: `Bearer ${token}`,
    'X-Tenant-ID': tenantId,
    Accept: 'application/json, text/csv, application/octet-stream',
    'X-Request-ID': testCase.id,
  };
  const body = testCase.body === null ? 'null' : undefined;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  const response = http.request(testCase.method, targetUrl(testCase), body, {
    headers,
    tags,
    timeout: '15s',
    responseCallback: http.expectedStatuses(...testCase.expectedStatuses),
  });

  let validResponse = false;
  if (response.status === 200) {
    if (testCase.responseKind === 'json') {
      try {
        const payload = response.json();
        validResponse = payload !== null && typeof payload === 'object';
      } catch { validResponse = false; }
    } else if (testCase.responseKind === 'csv') {
      validResponse = response.headers['Content-Type']?.includes('text/csv') && response.body.length > 0;
    } else {
      validResponse = response.body.length > 0 && Boolean(response.headers['Content-Type']);
    }
  } else {
    validResponse = response.body.length > 0;
  }

  const passed = check(response, {
    [`${testCase.id} · expected HTTP status`]: (r) => testCase.expectedStatuses.includes(r.status),
    [`${testCase.id} · ${testCase.responseKind} response`]: () => validResponse,
  }, tags);
  caseLatency.add(response.timings.duration, { ...tags, status: String(response.status) });
  caseFailures.add(!passed, { ...tags, status: String(response.status) });
  sleep(0.02);
}

export function handleSummary(data) {
  const jsonPath = __ENV.K6_SUMMARY_PATH || './report-output/native-k6-summary.json';
  return {
    [jsonPath]: JSON.stringify(data, null, 2),
    stdout: `Nexora One K6: ${data.metrics.iterations?.values?.count || 0} iterations · ${data.metrics.http_req_failed?.values?.rate || 0} unexpected request error rate\n`,
  };
}
