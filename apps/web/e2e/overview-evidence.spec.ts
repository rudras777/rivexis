import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
const wallet='0x'+'1'.repeat(40),instant=new Date('2026-10-18T03:00:00Z');
const snapshot=(changes:Record<string,unknown>={})=>({...sampleSnapshot(instant.getTime()),sample:false,wallet,blockNumber:'28000123',blockHash:'0x'+'1'.repeat(64),...changes});
async function setup(page:Page,data=snapshot(),fixed=true){
 await page.clock.install({time:instant});if(fixed)await page.clock.setFixedTime(instant);
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'QA',name:'QA workspace',role:'OWNER',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}}));
 await page.route('https://ethereum.publicnode.com/**',r=>r.abort('failed'));
 let reads=0;await page.route('**/api/v1/defi/snapshot',r=>{reads++;return r.fulfill({json:data})});
 return ()=>reads;
}
const metrics=(page:Page)=>page.getByRole('region',{name:'Current analysis overview',exact:true});
async function inspect(page:Page){await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByLabel('Public Ethereum address',{exact:true}).fill(wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(page.getByRole('button',{name:'Refresh evidence ↻',exact:true})).toBeVisible();await page.getByRole('link',{name:'Overview',exact:true}).click();await expect(metrics(page)).toBeVisible()}

test('Overview without inspection has no invented balances or block',async({page})=>{
 const reads=await setup(page);await page.goto('/workspace/overview',{waitUntil:'domcontentloaded'});await expect(metrics(page).locator('strong')).toHaveText(['—','—','—']);await expect(metrics(page).locator('small')).toHaveText(Array(3).fill('Inspect a wallet to view this metric'));expect(reads()).toBe(0);
});
for(const item of [
 {name:'recent snapshot',changes:{},hint:'Observed snapshot · 0s old',values:['$30,000.00','$18,000.00','#28000123']},
 {name:'zero balances',changes:{observedCollateralRaw:'0',observedDebtRaw:'0'},hint:'Observed snapshot · 0s old',values:['$0.00','$0.00','#28000123']},
 {name:'179 seconds remains observed',changes:{blockTimestamp:instant.getTime()/1000-179},hint:'Observed snapshot · 179s old',values:['$30,000.00','$18,000.00','#28000123']},
 {name:'expired evidence retains original values with stale labels',changes:{blockTimestamp:instant.getTime()/1000-181},hint:'Stale snapshot · refresh in LiquidationGuard',values:['$30,000.00','$18,000.00','#28000123']},
 {name:'unsupported response is not a verified summary',changes:{status:'UNSUPPORTED'},hint:'Unvalidated snapshot · inspect again',values:['—','—','—']},
 {name:'missing observation time is not current',changes:{blockTimestamp:0},hint:'Snapshot time unavailable · inspect again',values:['—','—','—']},
 {name:'null observation time is not current',changes:{blockTimestamp:null},hint:'Snapshot time unavailable · inspect again',values:['—','—','—']},
 {name:'future evidence is not current',changes:{blockTimestamp:instant.getTime()/1000+31},hint:'Snapshot time is ahead of this device · refresh evidence',values:['—','—','—']},
])test(`Overview provenance: ${item.name}`,async({page})=>{
 const reads=await setup(page,snapshot(item.changes));await inspect(page);await expect(metrics(page).locator('small')).toHaveText(Array(3).fill(item.hint));await expect(metrics(page).locator('strong')).toHaveText(item.values);expect(reads()).toBe(1);
});

test('Overview labels educational values and never invents an evidence block',async({page})=>{
 const reads=await setup(page);await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Explore a hypothetical sample',exact:true}).click();await expect(page.getByRole('cell',{name:'Hypothetical input',exact:true})).toHaveCount(2);await expect(page.getByRole('cell',{name:'Validated at snapshot',exact:true})).toHaveCount(0);await page.getByRole('link',{name:'Overview',exact:true}).click();await expect(metrics(page).locator('small')).toHaveText(Array(3).fill('Hypothetical sample · not live'));await expect(metrics(page).locator('strong')).toHaveText(['$30,000.00','$18,000.00','Not on-chain']);expect(reads()).toBe(0);
});

test('Overview ages an open inspection without extra financial RPC or data mutation',async({page})=>{
 const reads=await setup(page,snapshot(),false);await inspect(page);await expect(metrics(page)).toContainText('Observed snapshot');await page.clock.fastForward(181_000);await expect(metrics(page).locator('small')).toHaveText(Array(3).fill('Stale snapshot · refresh in LiquidationGuard'));await expect(metrics(page).locator('strong')).toHaveText(['$30,000.00','$18,000.00','#28000123']);expect(reads()).toBe(1);
 await page.getByRole('link',{name:'Inspect lending exposure',exact:true}).click();await expect(page.getByText('STALE SNAPSHOT',{exact:true})).toBeVisible();await expect(page.getByRole('cell',{name:'Validated at snapshot',exact:true})).toHaveCount(2);await expect(page.getByRole('cell',{name:'FRESH',exact:true})).toHaveCount(0);await page.getByRole('button',{name:'About oracle evidence',exact:true}).focus();await expect(page.getByRole('tooltip')).toContainText('not current freshness');await page.keyboard.press('Escape');await expect(page.getByRole('tooltip')).toBeHidden();expect(reads()).toBe(1);
});

test('Overview recalculates age after leaving and returning to the route',async({page})=>{
 const reads=await setup(page,snapshot(),false);await inspect(page);await page.getByRole('link',{name:'Manage wallet access',exact:true}).click();await expect(page).toHaveURL(/\/workspace\/wallets$/);await page.clock.fastForward(181_000);await page.getByRole('link',{name:'Overview',exact:true}).click();await expect(metrics(page).locator('small')).toHaveText(Array(3).fill('Stale snapshot · refresh in LiquidationGuard'));expect(reads()).toBe(1);
});

test('Overview keeps restored report evidence historical even when its timestamp is recent',async({page})=>{
 const reads=await setup(page);const receipt={snapshot:snapshot(),constraints:{budget:'3000',target:'1.50',gasReserve:'25',shocks:{},objective:'target'}};
 await page.route('**/api/v1/defi-reports',r=>r.fulfill({json:{items:[{id:'HISTORY_FIXTURE',created_at:instant.toISOString(),receipt}]}}));
 await page.goto('/workspace/reports',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Load saved reports',exact:true}).click();await page.getByRole('button',{name:'Open comparison →',exact:true}).click();await expect(page).toHaveURL(/\/workspace\/frontier$/);await page.getByRole('link',{name:'Overview',exact:true}).click();await expect(metrics(page).locator('small')).toHaveText(Array(3).fill('Historical receipt · refresh before analysis'));await expect(metrics(page).locator('strong')).toHaveText(['$30,000.00','$18,000.00','#28000123']);expect(reads()).toBe(0);
});

for(const width of [320,768,1440])test(`stale Overview evidence remains accessible without overflow at ${width}px`,async({page})=>{
 await setup(page,snapshot({blockTimestamp:instant.getTime()/1000-181}));await inspect(page);await page.setViewportSize({width,height:1000});
 await expect(metrics(page).locator('small')).toHaveText(Array(3).fill('Stale snapshot · refresh in LiquidationGuard'));
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
 expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([]);
});
