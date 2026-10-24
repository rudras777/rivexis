import { expect, test } from './browser-test';

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

test('recovery responses prevent forwarding token-bearing URLs in referrers before hydration',async({request})=>{
  const response=await request.get('/reset-password?token_hash=SYNTHETIC_HEADER_PROBE');
  expect(response.status()).toBe(200);
  expect(response.headers()['referrer-policy']).toBe('no-referrer');
});

test('login responses protect confirmation query credentials before hydration',async({request})=>{
  const response=await request.get('/login?access_token=SYNTHETIC_HEADER_PROBE');
  expect(response.status()).toBe(200);expect(response.headers()['referrer-policy']).toBe('no-referrer');
});

test('cross-site login is rejected before authentication or cookie creation',async({request})=>{
  const response=await request.post('/api/v1/auth/web/login',{headers:{origin:'https://untrusted.example','sec-fetch-site':'cross-site'},data:{}});
  expect(response.status()).toBe(403);expect(response.headers()['set-cookie']).toBeUndefined();expect(response.headers()['cache-control']).toBe('no-store');
});

test('origin mismatch is denied independently of fetch metadata',async({request})=>{
  const response=await request.patch('/api/v1/account/settings',{headers:{origin:'https://untrusted.example','sec-fetch-site':'same-origin'},data:{}});
  expect(response.status()).toBe(403);expect(response.headers()['set-cookie']).toBeUndefined();
});

test('oversized body is rejected before upstream authentication',async({request})=>{
  const response=await request.post('/api/v1/auth/web/login',{data:'x'.repeat(131073)});
  expect(response.status()).toBe(413);expect(response.headers()['set-cookie']).toBeUndefined();expect(response.headers()['cache-control']).toBe('no-store');
});
