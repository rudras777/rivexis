import {defineConfig,devices} from '@playwright/test';
import live from './playwright.live.config';

// The inherited live config requires the existing production URL and exact commit.
export default defineConfig({...live,timeout:90_000,retries:0,failOnFlakyTests:true,
  projects:[
    {name:'firefox',use:{...devices['Desktop Firefox']}},
    {name:'webkit',use:{...devices['Desktop Safari']}},
  ],
  reporter:[['list'],['json',{outputFile:'test-results/live-compatibility-results.json'}]],
});
