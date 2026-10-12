import {defineConfig,devices} from '@playwright/test';
// Fixture-driven browser certification against the owned local release build.
// External baseURL may be used for provider-only checks after deployment.
export default defineConfig({testDir:'./e2e',testMatch:'launch-account-connectivity.spec.ts',timeout:30_000,expect:{timeout:5_000},workers:2,reporter:[['list'],['json',{outputFile:'test-results/launch-account-results.json'}]],use:{baseURL:process.env.RIVEXIS_WEB_BASE_URL||'http://127.0.0.1:3000',trace:'retain-on-failure',screenshot:'only-on-failure'},projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}]});
