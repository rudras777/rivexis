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

const MUTATING_AUTH_FORMS = ['/login','/signup','/forgot-password','/verify-email','/reset-password'];

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

  for (const route of MUTATING_AUTH_FORMS) {
    test(`${route} never exposes mutation inputs through GET semantics`, async ({ page }) => {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      const forms=page.locator('form');
      await expect(forms.first()).toBeVisible();
      const count=await forms.count();
      for(let i=0;i<count;i++)await expect(forms.nth(i)).toHaveAttribute('method','post');
      const submitButtons=page.locator('form button[type="submit"]');
      expect(await submitButtons.count()).toBe(count);
    });
  }

  test('mobile header keeps navigation and login reachable', async ({ page }) => {
    await page.setViewportSize({width:390,height:844});
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const menu=page.locator('.mobileNav');
    await expect(menu).toBeVisible();
    await menu.locator('summary').click();
    await expect(menu.getByRole('link',{name:'Platform'})).toBeVisible();
    await expect(menu.getByRole('link',{name:'Log in'})).toBeVisible();
    await expect(menu.getByRole('link',{name:'Start workspace'})).toBeVisible();
  });

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
