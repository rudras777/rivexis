import {openWorkspaceView,mockWorkspaceAccess} from './workspace-test-navigation';
import {test,expect,type Route} from './browser-test';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';

const addressA='0x'+'1'.repeat(40),addressB='0x'+'2'.repeat(40);
function snapshot(wallet=addressA){return {...sampleSnapshot(),sample:false,wallet,blockTimestamp:Math.floor(Date.now()/1000)}}
test.beforeEach(async({page})=>{
 await mockWorkspaceAccess(page);
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
});

test('old wallet response cannot replace a newer inspection or unlock its button',async({page})=>{
 const pending:Route[]=[];await page.route('**/api/v1/defi/snapshot',r=>{pending.push(r)});
 await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByLabel('Public Ethereum address').fill(addressA);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect.poll(()=>pending.length).toBe(1);
 await page.getByLabel('Public Ethereum address').fill(addressB);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect.poll(()=>pending.length).toBe(2);
 const response=page.waitForResponse('**/api/v1/defi/snapshot');await pending[0].fulfill({json:snapshot(addressA)});await response;
 await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'Reading evidence…'})).toBeDisabled();
 await pending[1].fulfill({json:{...snapshot(addressB),observedCollateralRaw:'4200000000000'}});await expect(page.getByText('$42,000.00',{exact:true})).toBeVisible();await expect(page.getByLabel('Public Ethereum address')).toHaveValue(addressB);
});

test('a late inspection cannot overwrite an explicitly selected educational sample',async({page})=>{
 let pending:Route|undefined;await page.route('**/api/v1/defi/snapshot',r=>{pending=r});await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByLabel('Public Ethereum address').fill(addressA);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect.poll(()=>Boolean(pending)).toBe(true);
 await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await pending!.fulfill({json:snapshot()});await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE',{exact:true})).toBeVisible();await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toHaveCount(0);
});

for(const control of ['Token amount','Action','Asset','Transaction position'])for(const outcome of ['success','failure'])test(`${control} edit suppresses an obsolete transaction ${outcome}`,async({page})=>{
 const fixture=snapshot();fixture.positions.push({...fixture.positions[0],id:'second-position'});
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({json:fixture}));const pending:Route[]=[];await page.route('**/api/v1/defi/transaction',r=>{pending.push(r)});
 await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByLabel('Public Ethereum address').fill(addressA);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();await openWorkspaceView(page,'transactions');await page.getByLabel('Token amount').fill('1');await page.getByRole('button',{name:'Preview transaction ↗'}).click();await expect.poll(()=>pending.length).toBe(1);
 if(control==='Token amount')await page.getByLabel(control).fill('2');else if(control==='Action')await page.getByLabel(control,{exact:true}).selectOption('supply');else if(control==='Asset')await page.getByLabel(control,{exact:true}).selectOption(fixture.positions[0].reserves[0].asset);else await page.getByLabel(control).selectOption('second-position');
 await page.getByRole('button',{name:'Preview transaction ↗'}).click();await expect.poll(()=>pending.length).toBe(2);
 const response=page.waitForResponse('**/api/v1/defi/transaction');await pending[0].fulfill(outcome==='failure'?{status:503,json:{detail:'OBSOLETE_PROVIDER_ERROR'}}:{json:{status:'PREVIEW_ONLY',simulation:'SUCCEEDED_AT_BLOCK',blockNumber:'OBSOLETE_BLOCK',before:{healthFactorRaw:'1333333333333333333'},after:{healthFactorRaw:'1400000000000000000'},blockers:[],warnings:[]}});await response;
 await expect(page.getByRole('heading',{name:'SUCCEEDED AT BLOCK'})).toHaveCount(0);await expect(page.locator('.defiWorkspace [role=alert]')).toHaveCount(0);await expect(page.getByRole('button',{name:'Simulating…'})).toBeDisabled();
 await pending[1].fulfill({status:503,json:{detail:'CURRENT_PROVIDER_ERROR'}});await expect(page.locator('.defiWorkspace [role=alert]')).toHaveText('CURRENT_PROVIDER_ERROR');await expect(page.getByRole('button',{name:'Preview transaction ↗'})).toBeEnabled();
});

test('late refresh failure cannot mark a different wallet unavailable',async({page})=>{
 let count=0,pending:Route|undefined;await page.route('**/api/v1/defi/snapshot',r=>{if(++count===2){pending=r;return}return r.fulfill({json:snapshot()})});await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByLabel('Public Ethereum address').fill(addressA);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await page.getByRole('button',{name:'Refresh evidence ↻'}).click();await expect.poll(()=>Boolean(pending)).toBe(true);
 await page.getByLabel('Public Ethereum address').fill(addressB);await pending!.fulfill({status:503,json:{detail:'OBSOLETE_REFRESH_ERROR'}});await expect(page.locator('.defiWorkspace [role=alert]')).toHaveCount(0);await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeEnabled();
});

test('an obsolete report load cannot replace the current list or unlock its request',async({page})=>{
 const pending:Route[]=[];await page.route('**/api/v1/defi-reports',r=>{pending.push(r)});await page.goto('/workspace',{waitUntil:'domcontentloaded'});await openWorkspaceView(page,'reports');await page.getByRole('button',{name:'Load saved reports',exact:true}).click();await expect.poll(()=>pending.length).toBe(1);
 await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await openWorkspaceView(page,'reports');await page.getByRole('button',{name:'Load saved reports',exact:true}).click();await expect.poll(()=>pending.length).toBe(2);
 const response=page.waitForResponse('**/api/v1/defi-reports');await pending[0].fulfill({json:{items:[{id:'OBSOLETE_REPORT',created_at:new Date().toISOString(),receipt:{}}]}});await response;await expect(page.getByText('OBSOLETE_REPORT',{exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'Loading saved reports…',exact:true})).toBeDisabled();
 await pending[1].fulfill({json:{items:[{id:'CURRENT_REPORT',created_at:new Date().toISOString(),receipt:{}}]}});await expect(page.getByText('CURRENT_REPORT',{exact:true})).toBeVisible();
});

test('a stale save completion does not announce success for a replaced comparison',async({page})=>{
 let pending:Route|undefined;await page.route('**/api/v1/defi-reports',r=>{pending=r});await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await openWorkspaceView(page,'frontier');await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();await openWorkspaceView(page,'reports');
 const requests:string[]=[];page.on('request',request=>requests.push(new URL(request.url()).pathname));
 await page.evaluate(()=>{const events:unknown[]=[];(window as any).__saveClickEvidence=events;for(const type of ['pointerdown','pointerup','click'])document.addEventListener(type,event=>{const target=event.target as HTMLElement;events.push({type,button:target.closest('button')?.textContent?.trim(),tag:target.tagName})},true)});
 try{await page.getByRole('button',{name:'Save comparison to account',exact:true}).click();await expect.poll(()=>Boolean(pending)).toBe(true)}finally{
  console.info('SAVE_CLICK_EVIDENCE '+JSON.stringify({pending:!!pending,requests,dom:await page.evaluate(()=>({events:(window as any).__saveClickEvidence,scrollBehavior:getComputedStyle(document.documentElement).scrollBehavior,buttons:Array.from(document.querySelectorAll('.inlineActions button')).map(button=>({label:button.textContent?.trim(),disabled:(button as HTMLButtonElement).disabled,top:button.getBoundingClientRect().top})),errors:Array.from(document.querySelectorAll('.defiWorkspace [role=alert]')).map(element=>element.textContent)}))}));
 }
 await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();const response=page.waitForResponse('**/api/v1/defi-reports');await pending!.fulfill({json:{id:'OBSOLETE_SAVE'}});await response;await expect(page.locator('.defiWorkspace > .success[role=status]')).toHaveCount(0);await expect(page.getByText(/Report saved:/)).toHaveCount(0);await expect(page.locator('.defiWorkspace p[role=status]')).toHaveText('No background monitoring is active.');
});

for(const destination of ['Stress-test this position →','Open Defense Frontier →'])test(`inspected wallet stays visible after navigating with ${destination}`,async({page})=>{
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'QA',name:'QA workspace',role:'Individual',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:{...DEFAULT_PREFERENCES,walletAddresses:[addressB]}}}));
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({json:snapshot()}));
 await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByLabel('Public Ethereum address').fill(addressA);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:destination,exact:true}).click();await expect(page).toHaveURL(destination.startsWith('Stress')?/\/workspace\/scenarios$/:/\/workspace\/frontier$/);await expect(page.getByLabel('Public Ethereum address')).toHaveValue(addressA);await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();
});

for(const view of ['scenarios','frontier'] as const)test(`retained watch selection cannot relabel a different inspected wallet in ${view}`,async({page})=>{
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:{...DEFAULT_PREFERENCES,walletAddresses:[addressB]}}}));
 const inspected:string[]=[];
 await page.route('**/api/v1/defi/snapshot',r=>{const wallet=r.request().postDataJSON().wallet;inspected.push(wallet);return r.fulfill({json:snapshot(wallet)})});
 await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});
 await page.getByRole('button',{name:'Inspect',exact:true}).click();await expect(page).toHaveURL(/\/workspace$/);
 await expect(page.getByLabel('Public Ethereum address')).toHaveValue(addressB);expect(inspected).toEqual([]);
 await page.getByLabel('Public Ethereum address').fill(addressA);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();
 await openWorkspaceView(page,view);
 await expect(page.getByLabel('Public Ethereum address')).toHaveValue(addressA);await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();expect(inspected).toEqual([addressA]);
 await page.getByRole('button',{name:'Refresh evidence ↻',exact:true}).click();await expect.poll(()=>inspected.length).toBe(2);expect(inspected).toEqual([addressA,addressA]);await expect(page.getByLabel('Public Ethereum address')).toHaveValue(addressA);
});
