import { test as base, expect } from '@playwright/test';

const sensitiveKey = /authorization|cookie|token|secret|password|email|phone|personal|first.?name|last.?name|full.?name/i;
const sensitiveText = /\bBearer\s+[^\s"']+|\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\b(?:\+?\d[\d\s().-]{7,}\d)\b/gi;
const methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'fetch'];

function safeValue(value, key = '') {
  if (sensitiveKey.test(key)) return '[REDACTED]';
  if (Array.isArray(value)) return value.map((item) => safeValue(item));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([childKey, childValue]) => [childKey, safeValue(childValue, childKey)]));
  if (typeof value === 'string') return value.replace(sensitiveText, '[REDACTED]').slice(0, 20000);
  return value;
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    for (const key of [...url.searchParams.keys()]) if (sensitiveKey.test(key)) url.searchParams.set(key, '[REDACTED]');
    return `${url.origin}${url.pathname}${url.search}`;
  } catch { return String(value).replace(sensitiveText, '[REDACTED]'); }
}

export const test = base.extend({
  request: async ({ request }, use, testInfo) => {
    const calls = [];
    const observedRequest = new Proxy(request, {
      get(target, property) {
        const original = Reflect.get(target, property, target);
        if (!methods.includes(property) || typeof original !== 'function') return typeof original === 'function' ? original.bind(target) : original;
        return async (url, options = {}) => {
          const headers = options.headers || {};
          const safeHeaders = Object.fromEntries(Object.entries(headers).map(([key, value]) => [key, sensitiveKey.test(key) ? '[REDACTED]' : value]));
          const entry = {
            method: property.toUpperCase(),
            url: safeUrl(url),
            requestHeaders: safeHeaders,
            requestBody: safeValue(options.data ?? options.form ?? options.multipart ?? null),
          };
          const startedAt = Date.now();
          try {
            const response = await Reflect.apply(original, target, [url, options]);
            entry.status = response.status();
            entry.responseHeaders = { 'content-type': response.headers()['content-type'] || '', 'x-request-id': response.headers()['x-request-id'] || '' };
            entry.durationMs = Date.now() - startedAt;
            const body = await response.body().catch(() => Buffer.alloc(0));
            const text = body.toString('utf8');
            try { entry.responseBody = safeValue(JSON.parse(text)); }
            catch { entry.responseBody = text.replace(sensitiveText, '[REDACTED]').slice(0, 20000); }
            calls.push(entry);
            return response;
          } catch (error) {
            entry.durationMs = Date.now() - startedAt;
            entry.error = String(error?.message || error).replace(sensitiveText, '[REDACTED]');
            calls.push(entry);
            throw error;
          }
        };
      },
    });

    try { await use(observedRequest); }
    finally {
      const isEvidenceSuite = /^(?:API|DB) \|/i.test(testInfo.title);
      if (isEvidenceSuite) {
        const endpoint = testInfo.title.match(/\b(GET|POST|PUT|PATCH|DELETE|HEAD)\s+(\/[^\s|]+)/i);
        const context = {
          test: testInfo.title,
          suite: testInfo.titlePath.join(' › '),
          result: testInfo.status || 'skipped',
          endpoint: endpoint ? { method: endpoint[1].toUpperCase(), path: endpoint[2] } : null,
          apiBaseConfigured: Boolean(process.env.API_BASE_URL),
          tenantContextConfigured: Boolean(process.env.TENANT_ID && process.env.E2E_TOKEN),
          calls,
          note: calls.length ? 'Captured request/response details are sanitized.' : 'No request was sent in this run; inspect the skip reason and configure the required test service/credentials.',
        };
        await testInfo.attach('API / database execution context', {
          body: Buffer.from(JSON.stringify(context, null, 2)),
          contentType: 'application/json',
        });
      }
    }
  },
});

export { expect };
