import {defineConfig,devices} from '@playwright/test';
import base from './playwright.config';
export default defineConfig({...base,testMatch:['risk-atlas.spec.ts'],workers:1,retries:0,reporter:[['list'],['json',{outputFile:'test-results/risk-atlas-results.json'}]],projects:[{name:'chromium',use:{...devices['Desktop Chrome']}},{name:'edge',use:{...devices['Desktop Edge'],channel:'msedge'}}]});
