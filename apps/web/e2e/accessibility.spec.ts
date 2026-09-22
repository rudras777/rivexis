import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const ACCESSIBILITY_ROUTES = ['/', '/platform', '/methodology', '/security', '/login', '/signup'];

test.describe('WCAG automated accessibility', () => {
  for (const route of ACCESSIBILITY_ROUTES) {
    test(`${route} has no serious/critical axe violations`, async ({ page }) => {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
        .analyze();
      const blockers = results.violations.filter(v => v.impact === 'critical' || v.impact === 'serious');
      expect(blockers, JSON.stringify(blockers, null, 2)).toEqual([]);
    });
  }

  test('authorized workspace shell has no serious/critical axe violations', async ({ page }) => {
    await page.route('**/health', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: {
        'Access-Control-Allow-Origin': 'http://127.0.0.1:3000',
        'Access-Control-Allow-Credentials': 'true',
      },
      body: JSON.stringify({ status: 'ready' }),
    }));
    await page.route('**/api/v1/workspaces', route => route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: {
        'Access-Control-Allow-Origin': 'http://127.0.0.1:3000',
        'Access-Control-Allow-Credentials': 'true',
      },
      body: JSON.stringify({
        items: [{ id: 'w1', name: 'Primary Treasury', role: 'Individual', access_role: 'OWNER' }],
      }),
    }));

    await page.goto('/workspace', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('navigation', { name: 'Workspace' })).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const blockers = results.violations.filter(v => v.impact === 'critical' || v.impact === 'serious');
    expect(blockers, JSON.stringify(blockers, null, 2)).toEqual([]);
  });
});
