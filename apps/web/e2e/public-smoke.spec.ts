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

  test('degraded API availability is disclosed globally', async ({ page }) => {
    await page.route('**/health', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'degraded',
          reason: 'FastAPI runtime unavailable on the approved free-tier stack',
        }),
      }),
    );

    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const availability = page.getByTestId('service-availability');
    await expect(availability).toHaveAttribute('role', 'status');
    await expect(availability).toContainText('Service availability');
    await expect(availability).toContainText('authenticated workspace actions and live analyses are unavailable');
  });
});
