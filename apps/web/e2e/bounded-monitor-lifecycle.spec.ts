import {test,expect,type Page,type Route} from '@playwright/test';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';

const wallet='0x'+'1'.repeat(40),other='0x'+'2'.repeat(40),instant=new Date('2026-10-18T04:00:00Z');
const monitor=(page:Page)=>page.locator('section.instrumentPanel').filter({has:page.getByRole('heading',{name:'Check for changes, with limits.',exact:true})});
function snapshot(changes:Record<string,unknown>={}){return {...sampleSnapshot(instant.getTime()),sample:false,wallet,coverage:'aave',blockNumber:'28000200',blockHash:'0x'+'1'.repeat(64),...changes}}
async function setup(page:Page){
 await page.clock.install({time:instant});
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'QA',name:'QA workspace',access_role:'OWNER'},{id:'OTHER',name:'Other workspace',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}}));
 await page.route('https://ethereum.publicnode.com/**',r=>r.abort('failed'));
 let reads=0;const pending:Route[]=[];
 await page.route('**/api/v1/defi/snapshot',r=>{if(++reads===1)return r.fulfill({json:snapshot()});pending.push(r)});
 await page.goto('/workspace/reports');await page.getByLabel('Public Ethereum address',{exact:true}).fill(wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();
 return {pending,reads:()=>reads,respond:async(index:number,changes:Record<string,unknown>={})=>pending[index].fulfill({json:snapshot({blockTimestamp:Math.floor(await page.evaluate(()=>Date.now())/1000),blockNumber:String(28000201+index),blockHash:'0x'+String(index+2).repeat(64),...changes})})};
}
async function start(page:Page,pending:Route[]){await monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true}).click();await expect.poll(()=>pending.length).toBe(1);await expect(monitor(page).getByRole('status')).toHaveText('Reading check 1 of 5…')}

for(const input of ['wallet','coverage'])test(`monitor cancels its in-flight read immediately when ${input} changes`,async({page})=>{
 const api=await setup(page);await start(page,api.pending);
 if(input==='wallet')await page.getByLabel('Public Ethereum address',{exact:true}).fill(other);else await page.getByLabel('Protocol coverage',{exact:true}).selectOption('combined');
 await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeVisible();
 await expect(monitor(page).getByRole('status')).toContainText('inspected wallet or coverage changed');
 await api.respond(0,{observedCollateralRaw:'9900000000000'});await page.clock.runFor(1);
 await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toHaveCount(0);await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

test('monitor stops and aborts pending evidence as soon as the tab becomes hidden',async({page})=>{
 const api=await setup(page);await start(page,api.pending);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'hidden'});document.dispatchEvent(new Event('visibilitychange'))});
 await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeVisible();await expect(monitor(page).getByRole('status')).toContainText('tab is hidden');
 await api.respond(0);await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'visible'});document.dispatchEvent(new Event('visibilitychange'))});await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

test('choosing a hypothetical sample cannot be overwritten by pending monitoring evidence',async({page})=>{
 const api=await setup(page);await start(page,api.pending);await page.getByRole('button',{name:'Explore a hypothetical sample',exact:true}).click();
 await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeDisabled();await expect(monitor(page).getByRole('status')).toContainText('inspected wallet or coverage changed');
 await api.respond(0);await page.clock.runFor(1);await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE',{exact:true})).toBeVisible();await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

test('wallet context reset aborts monitoring immediately and does not reinstate cleared financial data',async({page})=>{
 const api=await setup(page);await start(page,api.pending);await page.evaluate(()=>window.dispatchEvent(new Event('rivexis-wallet-context-change')));
 await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeDisabled();await expect(monitor(page).getByRole('status')).toContainText('wallet access changed');
 await api.respond(0);await page.clock.runFor(1);await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toHaveCount(0);await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

test('switching the active workspace stops monitoring and discards its pending reply',async({page})=>{
 const api=await setup(page);await start(page,api.pending);await page.getByRole('combobox',{name:'ACTIVE WORKSPACE',exact:true}).selectOption('OTHER');
 await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeVisible();await expect(monitor(page).getByRole('status')).toContainText('active workspace changed');
 await api.respond(0,{observedCollateralRaw:'9900000000000'});await page.clock.runFor(1);await expect(page.locator('.evidenceStrip')).toContainText('Block 28000200');await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

test('explicit stop ignores a late reply and permits a clean explicit restart',async({page})=>{
 const api=await setup(page);await start(page,api.pending);await monitor(page).getByRole('button',{name:'Stop checks',exact:true}).click();await expect(monitor(page).getByRole('status')).toContainText('Checks stopped. Restart explicitly');
 await api.respond(0,{observedCollateralRaw:'9900000000000'});await page.clock.runFor(1);await expect(page.locator('.evidenceStrip')).toContainText('Block 28000200');
 await monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true}).click();await expect.poll(()=>api.pending.length).toBe(2);await api.respond(1);await expect(monitor(page).getByRole('status')).toHaveText('Check 1 of 5 complete. Latest block: 28000202.');
 await monitor(page).getByRole('button',{name:'Stop checks',exact:true}).click();await page.clock.fastForward(240000);expect(api.reads()).toBe(3);
});

test('leaving the monitoring view aborts its request and retains the last verified snapshot',async({page})=>{
 const api=await setup(page);await start(page,api.pending);await page.getByRole('link',{name:'Overview',exact:true}).click();await expect(page.getByRole('region',{name:'Current analysis overview'})).toBeVisible();
 await api.respond(0,{observedCollateralRaw:'9900000000000'});await page.clock.runFor(1);await expect(page.getByRole('region',{name:'Current analysis overview'}).locator('strong')).toHaveText(['$30,000.00','$18,000.00','#28000200']);await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

for(const status of [429,503])test(`monitor stops on provider/quota ${status} and only retries explicitly`,async({page})=>{
 const api=await setup(page);await start(page,api.pending);await api.pending[0].fulfill({status,json:{detail:status===429?'Beta analysis quota exhausted':'RPC evidence unavailable'}});
 await expect(monitor(page).getByRole('status')).toContainText(status===429?'Beta analysis quota exhausted':'RPC evidence unavailable');await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeEnabled();await expect(page.locator('.evidenceStrip')).toContainText('Block 28000200');
 await page.clock.fastForward(240000);expect(api.reads()).toBe(2);await monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true}).click();await expect.poll(()=>api.pending.length).toBe(2);await api.respond(1);await expect(monitor(page).getByRole('status')).toHaveText('Check 1 of 5 complete. Latest block: 28000202.');
});

test('a stalled monitoring request reaches its deadline and releases controls without retry',async({page})=>{
 const api=await setup(page);await start(page,api.pending);await page.clock.fastForward(35100);
 await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeEnabled();await expect(monitor(page).getByRole('status')).toContainText('timed out');await expect(monitor(page).getByRole('status')).toContainText('Monitoring stopped');await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});

test('monitor performs at most five checks and requires an explicit sixth-check restart',async({page})=>{
 const api=await setup(page);await start(page,api.pending);
 for(let index=0;index<5;index++){
  if(index){await page.clock.fastForward(120000);await expect.poll(()=>api.pending.length).toBe(index+1)}
  await api.respond(index);await expect(monitor(page).getByRole('status')).toHaveText(index===4?'Five checks complete. Monitoring stopped; restart explicitly if needed.':`Check ${index+1} of 5 complete. Latest block: ${28000201+index}.`);
 }
 await page.clock.fastForward(240000);expect(api.reads()).toBe(6);await monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true}).click();await expect.poll(()=>api.pending.length).toBe(6);await api.respond(5);await expect(monitor(page).getByRole('status')).toHaveText('Check 1 of 5 complete. Latest block: 28000206.');
});

for(const item of [
 {name:'another wallet',changes:{wallet:other},message:'did not match'},
 {name:'another coverage',changes:{coverage:'combined'},message:'did not match'},
 {name:'hypothetical response',changes:{sample:true},message:'did not match'},
 {name:'unsupported response',changes:{status:'UNSUPPORTED'},message:'unsupported'},
 {name:'expired response',changes:{blockTimestamp:instant.getTime()/1000-181},message:'stale or has an invalid observation time'},
 {name:'future response',changes:{blockTimestamp:instant.getTime()/1000+60},message:'stale or has an invalid observation time'},
 {name:'missing response time',changes:{blockTimestamp:0},message:'stale or has an invalid observation time'},
 {name:'invalid block identity',changes:{blockNumber:'unknown'},message:'invalid block identity'},
 {name:'older response block',changes:{blockNumber:'28000199'},message:'older monitoring evidence was discarded'},
])test(`monitor rejects ${item.name} without replacing verified evidence`,async({page})=>{
 const api=await setup(page);await start(page,api.pending);await api.respond(0,item.changes);
 await expect(monitor(page).getByRole('status')).toContainText(item.message);await expect(monitor(page).getByRole('button',{name:'Start five bounded checks',exact:true})).toBeEnabled();await expect(page.locator('.evidenceStrip')).toContainText('Block 28000200');await page.clock.fastForward(240000);expect(api.reads()).toBe(2);
});
