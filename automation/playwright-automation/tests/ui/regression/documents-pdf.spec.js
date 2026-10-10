import { test, expect } from '@playwright/test';
import { screenPageFor } from '../../../pages/index.js';
import { startLocalDemo } from '../../../utils/auth.js';

test('Documents | sample invoice PDF is available and readable', async ({ page, request, baseURL }) => {
  const documents = screenPageFor(page, 'documents');
  await startLocalDemo(page);
  await documents.open();
  await expect(documents.pageHeading).toHaveText('Documents');

  const response = await request.get(new URL('/demo-documents/invoice-nxo-1042.pdf', baseURL).toString());
  expect(response.ok()).toBe(true);
  expect(response.headers()['content-type']).toContain('application/pdf');
  expect((await response.body()).subarray(0, 5).toString()).toBe('%PDF-');
});
