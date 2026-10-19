import {defineConfig,devices} from '@playwright/test';
import base from './playwright.config';

// These authenticated workflows use controlled API/provider fixtures, never production.
const target=new URL(base.use?.baseURL??'http://127.0.0.1:3000');
if(!['localhost','127.0.0.1','[::1]'].includes(target.hostname))throw new Error('Compatibility fixtures require a local test server');

export default defineConfig({...base,timeout:90_000,retries:0,failOnFlakyTests:true,
  projects:[
    {name:'firefox',use:{...devices['Desktop Firefox']}},
    {name:'webkit',use:{...devices['Desktop Safari']}},
  ],
  reporter:[['list'],['json',{outputFile:'test-results/compatibility-results.json'}]],
});
