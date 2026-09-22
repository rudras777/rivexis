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
});
