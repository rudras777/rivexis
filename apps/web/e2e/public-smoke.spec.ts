import { expect, test } from '@playwright/test';

const PUBLIC_ROUTES = [
  '/',
  '/platform',
  '/blockchain-intelligence',
  '/crypto-finance',
  '/defi-risk',
  '/methodology',
  '/data',
  '/security',
  '/docs',
  '/pricing',
  '/login',
  '/signup',
];

test.describe('public route smoke', () => {
  for (const route of PUBLIC_ROUTES) {
    test(`${route} renders without page errors`, async ({ page }) => {
      const pageErrors: string[] = [];
      page.on('pageerror', error => pageErrors.push(error.message));
      const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
      expect(response, `missing navigation response for ${route}`).not.toBeNull();
      expect(response!.status(), `HTTP status for ${route}`).toBeLessThan(500);
      await expect(page.locator('body')).toBeVisible();
      expect(pageErrors).toEqual([]);
    });
  }
});
