import { expect, test } from '@playwright/test';

test('public responses carry the baseline browser security headers', async ({ request }) => {
  const response = await request.get('/');
  expect(response.status()).toBeLessThan(500);
  const headers = response.headers();
  expect(headers['x-content-type-options']).toBe('nosniff');
  expect(headers['x-frame-options']).toBe('DENY');
  expect(headers['referrer-policy']).toBe('strict-origin-when-cross-origin');
  expect(headers['permissions-policy']).toContain('camera=()');
  expect(headers['permissions-policy']).toContain('microphone=()');
  expect(headers['permissions-policy']).toContain('geolocation=()');
  expect(headers['x-powered-by']).toBeUndefined();
});
