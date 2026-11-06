import base from './playwright.config';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

const manifest=JSON.parse(readFileSync(new URL('./dist/server/rivexis-public-document.json',import.meta.url),'utf8')) as {build:string;documents?:{pathname:string}[]};
if(!manifest.build||!manifest.documents?.some(document=>document.pathname==='/forgot-password'))throw new Error('Build the compiled recovery document before Worker acceptance');
if(process.env.RIVEXIS_EXPECTED_BUILD_SHA&&process.env.RIVEXIS_EXPECTED_BUILD_SHA!==manifest.build)throw new Error('The compiled Worker differs from the expected build');
process.env.RIVEXIS_EXPECTED_BUILD_SHA=manifest.build;

export default {...base,
  testMatch:['production-public-regressions.spec.ts','account-settings.spec.ts'],
  grep:/auth and recovery forms|compiled recovery document|Settings and recovery retry links/,
  workers:1,retries:0,
  outputDir:'test-results/worker-public',
  reporter:[['list'],['json',{outputFile:'test-results/worker-public-results.json'}]],
  use:{...base.use,baseURL:'http://127.0.0.1:3016'},
  webServer:{
    command:'npm exec -- wrangler dev --config dist/server/wrangler.json --local --ip 127.0.0.1 --port 3016 --inspector-port 0 --var RIVEXIS_E2E_BLOCK_EXTERNAL_UPSTREAM:1 --show-interactive-dev-session=false --log-level error',
    cwd:fileURLToPath(new URL('.',import.meta.url)),
    url:'http://127.0.0.1:3016',reuseExistingServer:false,timeout:60000,
    env:{WRANGLER_SEND_METRICS:'false',CI:'true'},
  },
};
