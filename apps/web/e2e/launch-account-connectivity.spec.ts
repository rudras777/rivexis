import {test,expect,type Page} from '@playwright/test';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
const address='0x'+'1'.repeat(40);
async function setup(page:Page){
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'OWNER',name:'Primary workspace',role:'Individual',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'Analyst',email:'qa@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}}));
}
async function provider(page:Page,scenario:string){await page.addInitScript(({address,scenario})=>{
 const listeners:Record<string,((value:unknown)=>void)[]>={};let chains=0;
 (window as any).walletMethods=[];(window as any).emitLaunchWallet=(name:string,value:unknown)=>(listeners[name]||[]).forEach(fn=>fn(value));
 const injected={request:async({method}:{method:string})=>{
  (window as any).walletMethods.push(method);
  if(method==='eth_chainId'){chains++;return scenario==='wrong network'||(scenario==='network race'&&chains>1)?'0x89':'0x1'}
  if(scenario==='declined')throw {code:4001};if(scenario==='pending')throw {code:-32002};if(scenario==='provider outage')throw Error('RPC down');
  return scenario==='empty account'?[]:scenario==='malformed account'?['private key']:scenario==='zero account'?['0x'+'0'.repeat(40)]:[address];
 },on:(event:string,fn:(value:unknown)=>void)=>{(listeners[event]??=[]).push(fn)},removeListener:(event:string,fn:(value:unknown)=>void)=>{listeners[event]=(listeners[event]||[]).filter(x=>x!==fn)}};
 window.addEventListener('eip6963:requestProvider',()=>window.dispatchEvent(new CustomEvent('eip6963:announceProvider',{detail:{info:{uuid:'launch-fixture',name:'Launch fixture'},provider:injected}})));
 },{address,scenario})}
async function choose(page:Page){await page.getByRole('button',{name:'Connect Wallet',exact:true}).click();await page.getByRole('button',{name:'Launch fixture',exact:true}).click()}
for(const [scenario,message] of [['wrong network','Choose Ethereum'],['network race','Network changed'],['empty account','valid Ethereum'],['malformed account','valid Ethereum'],['zero account','valid Ethereum'],['declined','declined'],['pending','already pending'],['provider outage','failed']])test('wallet fixture: '+scenario,async({page})=>{
 await setup(page);await provider(page,scenario);await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await expect(page.getByRole('dialog')).toContainText(message);await expect(page.getByRole('button',{name:'Forget wallet access'})).toHaveCount(0);
 const methods=await page.evaluate(()=>(window as any).walletMethods);expect(methods).not.toEqual(expect.arrayContaining(['eth_sendTransaction','personal_sign','eth_sign','wallet_switchEthereumChain']));if(scenario==='wrong network')expect(methods).toEqual(['eth_chainId']);
});
test('wallet fixture: disconnect and explicit repeated connection',async({page})=>{
 await setup(page);await provider(page,'success');await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});expect(await page.evaluate(()=>(window as any).walletMethods)).toEqual([]);await choose(page);await expect(page.locator('.connectionPanel')).toContainText(address);await page.evaluate(()=>(window as any).emitLaunchWallet('disconnect',{}));await expect(page.locator('.connectionPanel')).toContainText('disconnected');await expect(page.getByRole('button',{name:'Forget wallet access'})).toHaveCount(0);await choose(page);await expect(page.locator('.connectionPanel')).toContainText(address);await page.getByRole('button',{name:'Forget wallet access'}).click();await expect(page.locator('.connectionPanel')).toContainText('Existing wallet permissions remain');
});
test('wallet fixture: empty account event removes financial context',async({page})=>{await setup(page);await provider(page,'success');await page.goto('/workspace/wallets',{waitUntil:'domcontentloaded'});await choose(page);await page.evaluate(()=>(window as any).emitLaunchWallet('accountsChanged',[]));await expect(page.locator('.connectionPanel')).toContainText('no longer exposes');await expect(page.getByRole('button',{name:'Forget wallet access'})).toHaveCount(0)});
test('logout provider failure clears private UI and shows truthful revocation warning',async({page})=>{
 await setup(page);await page.route('**/api/v1/auth/logout',r=>{expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');return r.fulfill({json:{status:'browser_session_cleared',refreshSessionRevoked:false}})});
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await page.getByLabel('Account menu',{exact:true}).click();await page.getByRole('button',{name:'Log out',exact:true}).click();await expect(page.getByRole('heading',{name:'Browser signed out'})).toBeVisible();await expect(page.locator('[data-testid="workspace-shell-session"]')).toContainText('could not confirm revocation');await expect(page.getByLabel('Display name')).toHaveCount(0);expect(await page.evaluate(()=>localStorage.getItem('rivexis_workspace_id'))).toBeNull();
});
