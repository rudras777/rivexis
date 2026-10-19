import {test,expect,type Page} from './browser-test';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
const address='0x'+'1'.repeat(40);
async function setup(page:Page,stages:number[]){
 await page.clock.install();
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'QA',name:'QA workspace',role:'OWNER',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}}));
 await page.route('**/api/v1/auth/logout',r=>r.fulfill({json:{status:'browser_session_cleared',refreshSessionRevoked:false}}));
 await page.addInitScript(({address,stages})=>{
  const calls:string[]=[],pending=new Map<number,()=>void>();
  (window as any).walletLifecycleCalls=calls;
  (window as any).releaseWalletLifecycle=(stage:number)=>{pending.get(stage)?.();pending.delete(stage)};
  const provider={request:async({method}:{method:string})=>{
   calls.push(method);const value=method==='eth_requestAccounts'?[address]:'0x1';
   if(stages.includes(calls.length))return new Promise(resolve=>pending.set(calls.length,()=>resolve(value)));
   return value;
  }};
  (window as any).ethereum=provider;
  window.addEventListener('eip6963:requestProvider',()=>window.dispatchEvent(new CustomEvent('eip6963:announceProvider',{detail:{info:{uuid:'deadline-fixture',name:'Deadline fixture'},provider}})));
 },{address,stages});
}
const calls=(page:Page)=>page.evaluate(()=>(window as any).walletLifecycleCalls as string[]);
const release=(page:Page,stage:number)=>page.evaluate(value=>(window as any).releaseWalletLifecycle(value),stage);
async function choose(page:Page){await page.getByRole('button',{name:'Connect Wallet',exact:true}).click();await page.getByRole('button',{name:'Deadline fixture',exact:true}).click()}
async function settings(page:Page){await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await page.getByRole('tab',{name:'Connected Wallets',exact:true}).click();await page.getByRole('button',{name:'Select browser wallet address',exact:true}).click()}

for(const stage of [1,2,3])test(`wallet deadline: stalled provider stage ${stage} releases controls and ignores late approval`,async({page})=>{
 await setup(page,[stage]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(stage);
 await page.clock.fastForward(35_100);await expect(page.getByRole('dialog')).toContainText('Wallet connection timed out');await expect(page.getByRole('dialog')).toContainText('may still be pending');
 await expect(page.getByRole('button',{name:'Deadline fixture',exact:true})).toBeEnabled();await release(page,stage);
 await expect(page.getByRole('button',{name:'Forget wallet access',exact:true})).toHaveCount(0);expect((await calls(page)).length).toBe(stage);
});
test('wallet deadline: one total deadline spans slow chain and permission stages',async({page})=>{
 await setup(page,[1,2]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(1);
 await page.clock.fastForward(20_000);await release(page,1);await expect.poll(async()=> (await calls(page)).length).toBe(2);
 await page.clock.fastForward(15_100);await expect(page.getByRole('dialog')).toContainText('Wallet connection timed out');expect((await calls(page)).length).toBe(2);
});
test('wallet cancellation: closing before chain read resolves prevents a later permission prompt and permits explicit retry',async({page})=>{
 await setup(page,[1]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(1);
 await page.getByRole('button',{name:'Close wallet selection',exact:true}).click();await expect(page.getByRole('dialog')).toBeHidden();await release(page,1);expect(await calls(page)).toEqual(['eth_chainId']);
 await choose(page);await expect(page.getByRole('dialog')).toBeHidden();await expect(page.getByRole('button',{name:'Forget wallet access',exact:true})).toBeVisible();expect(await calls(page)).toEqual(['eth_chainId','eth_chainId','eth_requestAccounts','eth_chainId']);
});
test('wallet cancellation: Escape ignores a late address grant without claiming permission revocation',async({page})=>{
 await setup(page,[2]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(2);
 await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toBeHidden();await release(page,2);await expect(page.locator('.connectionPanel')).toContainText('may still be pending');await expect(page.getByRole('button',{name:'Forget wallet access'})).toHaveCount(0);expect((await calls(page)).length).toBe(2);
});
test('wallet cancellation: logout stops the pending chain check before account permission is requested',async({page})=>{
 await setup(page,[1]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(1);
 await page.evaluate(()=>window.dispatchEvent(new Event('rivexis-request-logout')));await expect(page.getByRole('heading',{name:'Browser signed out'})).toBeVisible();await release(page,1);expect(await calls(page)).toEqual(['eth_chainId']);await expect(page.locator('.connectionPanel')).toHaveCount(0);
});
test('wallet retry: timed-out permission is not auto-retried and a new explicit request can succeed',async({page})=>{
 await setup(page,[2]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(2);
 await page.clock.fastForward(35_100);await expect(page.getByRole('dialog')).toContainText('timed out');await page.clock.fastForward(60_000);expect((await calls(page)).length).toBe(2);
 await page.getByRole('button',{name:'Deadline fixture',exact:true}).click();await expect(page.getByRole('dialog')).toBeHidden();await expect(page.locator('.connectionPanel')).toContainText(address);await release(page,2);expect((await calls(page)).length).toBe(5);
 await page.clock.fastForward(40_000);await expect(page.getByRole('button',{name:'Forget wallet access'})).toBeVisible();
});
test('Settings deadline: a stalled provider releases the selector and cannot select a late address',async({page})=>{
 await setup(page,[2]);await settings(page);await expect.poll(async()=> (await calls(page)).length).toBe(2);
 await page.clock.fastForward(35_100);await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('timed out');await expect(page.getByRole('button',{name:'Select browser wallet address'})).toBeEnabled();
 await release(page,2);await expect(page.locator('.selectedWallet')).toHaveCount(0);expect((await calls(page)).length).toBe(2);
 await page.getByRole('button',{name:'Select browser wallet address'}).click();await expect(page.locator('.selectedWallet')).toContainText(address);expect((await calls(page)).length).toBe(5);
});
test('Settings cancellation: changing section prevents a delayed account-permission request',async({page})=>{
 await setup(page,[1]);await settings(page);await expect.poll(async()=> (await calls(page)).length).toBe(1);
 await page.getByRole('tab',{name:'Privacy',exact:true}).click();await release(page,1);expect(await calls(page)).toEqual(['eth_chainId']);
 await page.getByRole('tab',{name:'Connected Wallets',exact:true}).click();await expect(page.getByRole('button',{name:'Select browser wallet address'})).toBeEnabled();await expect(page.locator('.selectedWallet')).toHaveCount(0);
});
test('Settings cancellation: navigation unmount stops pending requests and discards late results',async({page})=>{
 await setup(page,[1]);await settings(page);await expect.poll(async()=> (await calls(page)).length).toBe(1);
 await page.getByLabel('Account menu',{exact:true}).click();await page.getByRole('link',{name:'Workspaces & organizations',exact:true}).click();await expect(page).toHaveURL(/settings\/workspaces$/);
 await release(page,1);expect(await calls(page)).toEqual(['eth_chainId']);
});
test('wallet cancellation: forgetting access while pending blocks every later provider stage',async({page})=>{
 await setup(page,[2]);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect.poll(async()=> (await calls(page)).length).toBe(2);
 await page.evaluate(()=>window.dispatchEvent(new Event('rivexis-wallet-forget')));await release(page,2);await expect(page.getByRole('dialog')).toContainText('Wallet access forgotten');await expect(page.getByRole('button',{name:'Deadline fixture'})).toBeEnabled();expect((await calls(page)).length).toBe(2);
});
