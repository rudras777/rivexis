import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.RIVEXIS_WEB_BASE_URL || 'http://127.0.0.1:3000';
const external = Boolean(process.env.RIVEXIS_WEB_BASE_URL);

export default defineConfig({
  testDir: './e2e',
  testMatch: ['service-availability.spec.ts','public-entry-loading.spec.ts','health-chart-precision.spec.ts','bounded-monitor-lifecycle.spec.ts','overview-evidence.spec.ts','wallet-request-lifecycle.spec.ts','morpho-defense-sequence.spec.ts','defense-sequence.spec.ts','financial-request-context.spec.ts','request-deadlines.spec.ts','launch-market.spec.ts','launch-account-connectivity.spec.ts','launch-charts.spec.ts','workspace-connectivity.spec.ts','blockchain-background.spec.ts','account-settings.spec.ts','institutional-completion.spec.ts','entry-experience.spec.ts','defi-product.spec.ts','browser-auth.spec.ts','session-lifecycle.spec.ts','security.spec.ts','history-provenance.spec.ts','organization-workspace-create.spec.ts','organization-scope-switching.spec.ts','saved-analysis-actions.spec.ts'],
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  workers: 2,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  failOnFlakyTests: Boolean(process.env.CI),
  reporter: [['list'], ['json', { outputFile: 'test-results/playwright-results.json' }]],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: external ? undefined : {
    command: 'npm run start',
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      RIVEXIS_E2E_BLOCK_EXTERNAL_UPSTREAM: '1',
    },
  },
});
