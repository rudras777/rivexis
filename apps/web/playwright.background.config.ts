import {defineConfig,devices} from '@playwright/test';
import base from './playwright.config';
export default defineConfig({...base,testMatch:['blockchain-background.spec.ts'],workers:1,retries:0,reporter:[['list'],['json',{outputFile:'test-results/background-results.json'}]],projects:[{name:'chromium',use:{...devices['Desktop Chrome']}},{name:'edge',use:{...devices['Desktop Edge'],channel:'msedge'}}]});
