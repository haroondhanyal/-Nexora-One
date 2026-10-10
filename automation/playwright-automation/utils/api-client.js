export function tenantHeaders({ token, tenantId, includeAuth = true, includeTenant = true } = {}) {
  const headers = { Accept: 'application/json' };
  if (includeAuth && token) headers.Authorization = `Bearer ${token}`;
  if (includeTenant && tenantId) headers['X-Tenant-ID'] = tenantId;
  return headers;
}

export function safeRequestLog({ caseId, method, path, tenantId, status, durationMs, requestId }) {
  return {
    caseId, method, path,
    tenantId: tenantId ? `${tenantId.slice(0, 8)}…` : 'missing',
    status, durationMs, requestId: requestId || 'not provided',
  };
}
