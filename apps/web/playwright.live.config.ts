import {defineConfig} from '@playwright/test';
import base from './playwright.config';
if(!['https://rivexis-web.rudrasingh0718.workers.dev','https://rivexis.rvea.info'].includes(process.env.RIVEXIS_WEB_BASE_URL??''))throw new Error('Live verification requires an exact approved production URL');
if(!/^[0-9a-f]{40}$/.test(process.env.RIVEXIS_EXPECTED_BUILD_SHA??''))throw new Error('Live verification requires the intended commit SHA');
export default defineConfig({...base,testMatch:['security.spec.ts','workspace-live.spec.ts','live-completion.spec.ts','production-public-regressions.spec.ts','blockchain-background-live.spec.ts','public-entry-loading.spec.ts'],workers:1,retries:0,webServer:undefined,reporter:[['list'],['json',{outputFile:'test-results/live-completion-results.json'}]]});
