import {test,expect,type Page} from './browser-test';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
const inactive={runtime:{state:'INACTIVE',email:false,interval_minutes:30,last_cycle_at:null},rule:null,events:[]};
const scheduled=()=>({...inactive,runtime:{state:'SCHEDULED',email:false,interval_minutes:30,last_cycle_at:new Date().toISOString()}});
async function account(page:Page,theme='dark'){
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'OWNER',name:'Synthetic QA workspace',role:'Individual',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'Synthetic QA',email:'qa@example.invalid',emailVerified:true},preferences:{...DEFAULT_PREFERENCES,theme,motion:'reduce'}}}));
 await page.route('**/api/v1/defi-reports',r=>r.fulfill({json:{items:[]}}));
 await page.route('https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js',r=>r.fulfill({contentType:'application/javascript',body:'/* isolated display-loader fixture; no market data */'}));
}
test('scheduled monitoring inactive has no opt-in or false coverage claim',async({page})=>{
 await account(page);await page.route('**/api/v1/defi/monitor',r=>r.fulfill({json:inactive}));await page.goto('/workspace/reports');
 const panel=page.getByRole('region',{name:'Scheduled risk monitoring'});await expect(panel).toContainText('Scheduled monitoring inactive');await expect(panel.getByRole('checkbox')).toHaveCount(0);await expect(panel).toContainText('Never');await expect(page.getByRole('button',{name:'Start five bounded checks'})).toBeVisible();
});
test('scheduled monitoring requires explicit opt-in and does not enroll existing accounts',async({page})=>{
 await account(page);let writes=0;
 await page.route('**/api/v1/defi/monitor',async r=>{if(r.request().method()==='PATCH'){writes++;const input=r.request().postDataJSON();expect(input.enabled).toBe(false);expect(input.emailOptIn).toBe(false);expect(input.owner).toBeUndefined();expect(input.recipient).toBeUndefined();expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');return r.fulfill({json:{...scheduled(),rule:{wallet:input.wallet,coverage:input.coverage,threshold_raw:'1200000000000000000',recovery_raw:'1300000000000000000',enabled:false,email_opt_in:false,last_status:'NEVER_EVALUATED',last_success_at:null,last_attempt_at:null,block_number:null,block_hash:null,condition:'UNKNOWN',health_raw:null,next_evaluation_at:new Date().toISOString()}}})}return r.fulfill({json:scheduled()})});
 await page.goto('/workspace/reports');const panel=page.getByRole('region',{name:'Scheduled risk monitoring'});await expect(panel).toContainText('Scheduled worker available');for(const box of await panel.getByRole('checkbox').all())await expect(box).not.toBeChecked();expect(writes).toBe(0);
 await panel.getByLabel('Public Ethereum address').fill('0x'+'a'.repeat(40));await panel.getByRole('button',{name:'Save monitoring preferences'}).click();await expect(panel).toContainText('Monitoring preferences saved');expect(writes).toBe(1);
});
test('unknown monitoring save outcome is held without retries or a success notice',async({page})=>{
 await account(page);let writes=0;await page.route('**/api/v1/defi/monitor',r=>{if(r.request().method()==='PATCH'){writes++;return r.fulfill({status:503,json:{detail:'Unconfirmed fixture write'}})}return r.fulfill({json:scheduled()})});
 await page.goto('/workspace/reports');const panel=page.getByRole('region',{name:'Scheduled risk monitoring'});await panel.getByLabel('Public Ethereum address').fill('0x'+'a'.repeat(40));await panel.getByRole('button',{name:'Save monitoring preferences'}).click();await expect(panel.getByRole('alert')).toContainText('Reload monitoring records before retrying');expect(writes).toBe(1);await expect(panel).not.toContainText('preferences saved');
});
test('stale scheduled heartbeat never presents current worker availability',async({page})=>{
 await account(page);await page.route('**/api/v1/defi/monitor',r=>r.fulfill({json:{...scheduled(),runtime:{...scheduled().runtime,last_cycle_at:new Date(Date.now()-901000).toISOString()}}}));await page.goto('/workspace/reports');const panel=page.getByRole('region',{name:'Scheduled risk monitoring'});await expect(panel).toContainText('Scheduled monitoring inactive');await expect(panel.getByRole('checkbox')).toHaveCount(0);
});
test('official market embed is lazy, sandboxed, single and cleaned up on close and navigation',async({page})=>{
 await account(page);await page.goto('/workspace/overview');const widget=page.locator('.exchangeChart');await expect(widget.locator('iframe')).toHaveCount(0);await widget.locator('summary').click();await expect(widget.locator('iframe')).toHaveCount(1);await expect(widget.locator('iframe')).toHaveAttribute('sandbox','allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox');await expect(widget.locator('iframe')).toHaveAttribute('src',/^data:text\/html;charset=utf-8,/);await expect(widget.locator('iframe')).toHaveAttribute('src',/BITSTAMP%3ABTCUSD/);await expect.poll(()=>widget.locator('iframe').evaluate((el:HTMLIFrameElement)=>el.contentDocument===null)).toBe(true);
 await widget.getByLabel('Market pair').selectOption('ETH');await expect(widget.locator('iframe')).toHaveCount(1);await expect(widget.locator('iframe')).toHaveAttribute('src',/BITSTAMP%3AETHUSD/);await widget.locator('summary').click();await expect(widget.locator('iframe')).toHaveCount(0);await page.goto('/workspace/networks');await expect(page.locator('.exchangeChart')).toHaveCount(0);
});
for(const width of [390,1440])for(const theme of ['light','dark'])test(`market and monitoring responsive ${width}px ${theme}`,async({page})=>{
 await page.setViewportSize({width,height:900});await account(page,theme);await page.route('**/api/v1/defi/monitor',r=>r.fulfill({json:scheduled()}));
 await page.goto('/workspace/reports');await expect(page.getByRole('region',{name:'Scheduled risk monitoring'})).toContainText('Scheduled worker available');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await page.goto('/workspace/overview');await page.locator('.exchangeChart > summary').click();await expect(page.getByLabel('Market pair')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
