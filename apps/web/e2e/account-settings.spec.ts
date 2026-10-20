import {test,expect,type Page} from './browser-test';
import AxeBuilder from '@axe-core/playwright';
import {DEFAULT_PREFERENCES,validateAccountUpdate} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
const address='0x'+'1'.repeat(40);
async function setup(page:Page){
 let account={profile:{displayName:'Analyst',email:'qa@example.invalid',emailVerified:true,createdAt:'2026-01-01T00:00:00Z',lastSignInAt:'2026-10-10T00:00:00Z'},preferences:structuredClone(DEFAULT_PREFERENCES)};
 const updates:unknown[]=[],sessionRequests:unknown[]=[];let fail=false;
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'SETTINGS_OWNER',name:'Primary workspace',role:'Individual',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>{
  if(r.request().method()==='PATCH'){updates.push(r.request().postDataJSON());expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');if(fail)return r.fulfill({status:503,json:{detail:'Unavailable'}});const input=validateAccountUpdate(r.request().postDataJSON());account={profile:{...account.profile,displayName:input.displayName??account.profile.displayName},preferences:input.preferences??account.preferences};}
  return r.fulfill({json:account});
 });
 await page.route('**/api/v1/account/sessions/others',r=>{sessionRequests.push(r.request().postDataJSON());return r.fulfill({json:{status:'other_refresh_sessions_revoked',accessTokensMayRemainValidUntilExpiry:true}})});
 await page.route('**/api/v1/account/export',r=>r.fulfill({json:{...account,reports:[{id:'OWN_REPORT',receipt:{blockNumber:'18001'}}]}}));
 return {updates,sessionRequests,setFailure:(value:boolean)=>{fail=value}};
}
async function tab(page:Page,name:string){await page.getByRole('tab',{name,exact:true}).click()}
async function save(page:Page){await page.getByRole('button',{name:'Save changes',exact:true}).click();await expect(page.getByRole('status').filter({hasText:'Account settings saved'})).toBeVisible()}

const validAccount=()=>({profile:{displayName:'Recovered analyst',email:'qa@example.invalid',emailVerified:true},preferences:structuredClone(DEFAULT_PREFERENCES)});
const malformedAccounts:[string,()=>unknown][]=[
 ['missing profile',()=>({preferences:DEFAULT_PREFERENCES})],
 ['null body',()=>null],
 ['array body',()=>[]],
 ['wrong verification type',()=>({...validAccount(),profile:{...validAccount().profile,emailVerified:'true'}})],
 ['missing preferences',()=>({profile:validAccount().profile})],
 ['partial preferences',()=>({...validAccount(),preferences:{theme:'dark'}})],
 ['unsupported appearance',()=>({...validAccount(),preferences:{...DEFAULT_PREFERENCES,theme:'unexpected'}})],
 ['nondecimal budget',()=>({...validAccount(),preferences:{...DEFAULT_PREFERENCES,defaultBudget:'NaN'}})],
 ['fee above capital',()=>({...validAccount(),preferences:{...DEFAULT_PREFERENCES,defaultBudget:'1',defaultFee:'25'}})],
 ['zero saved identity',()=>({...validAccount(),preferences:{...DEFAULT_PREFERENCES,walletAddresses:['0x'+'0'.repeat(40)]}})],
];
for(const [label,malformed] of malformedAccounts)test(`malformed successful Settings response: ${label} fails safely and allows recovery`,async({page})=>{
 await setup(page);let healthy=false,reads=0;const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.route('**/api/v1/account/settings',r=>{expect(r.request().method()).toBe('GET');reads++;return r.fulfill({json:healthy?validAccount():malformed()})});
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});
 await expect(page.getByRole('alert').filter({hasText:'Account settings are unavailable'})).toBeVisible();
 await expect(page.getByLabel('Display name')).toHaveCount(0);expect(errors).toEqual([]);const initial=reads;expect(initial).toBeGreaterThanOrEqual(1);expect(initial).toBeLessThanOrEqual(2);
 healthy=true;await page.getByRole('button',{name:'Retry settings',exact:true}).click();
 await expect(page.getByLabel('Display name')).toHaveValue('Recovered analyst');expect(reads).toBe(initial+1);expect(errors).toEqual([]);
});

for(const fault of ['degraded503','transport','malformed-json'])test(`Settings read recovers explicitly after ${fault} without any writes`,async({page})=>{
 await setup(page);let healthy=false,reads=0,writes=0;
 await page.route('**/api/v1/account/settings',r=>{
  if(r.request().method()!=='GET'){writes++;return r.fulfill({status:500})}reads++;
  if(healthy)return r.fulfill({json:validAccount()});
  if(fault==='transport')return r.abort('failed');
  if(fault==='malformed-json')return r.fulfill({contentType:'application/json',body:'{'});
  return r.fulfill({status:503,headers:{'sb-error-code':'SUPABASE_EDGE_RUNTIME_SERVICE_DEGRADED'},json:{detail:'Provider temporarily unavailable'}});
 });
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await expect(page.getByRole('button',{name:'Retry settings',exact:true})).toBeEnabled();const initial=reads;
 healthy=true;await page.getByRole('button',{name:'Retry settings',exact:true}).click();await expect(page.getByLabel('Display name')).toHaveValue('Recovered analyst');expect(reads).toBe(initial+1);expect(writes).toBe(0);
});

test('unverified save confirmation retains the draft and requires an explicit write retry',async({page})=>{
 await setup(page);let writes=0;
 await page.route('**/api/v1/account/settings',r=>{
  if(r.request().method()==='GET')return r.fulfill({json:validAccount()});
  writes++;expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');
  return r.fulfill({json:writes===1?{status:'ok'}:{...validAccount(),profile:{...validAccount().profile,displayName:'Draft retained'}}});
 });
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await page.getByLabel('Display name').fill('Draft retained');await page.getByRole('button',{name:'Save changes',exact:true}).click();
 await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('could not be confirmed');await expect(page.getByLabel('Display name')).toHaveValue('Draft retained');await expect(page.locator('.settingsFeedback [role=status]')).toHaveCount(0);expect(writes).toBe(1);
 await save(page);expect(writes).toBe(2);await expect(page.getByRole('button',{name:'Save changes',exact:true})).toBeDisabled();
});

test('saved identity validation rejects zero and bad checksum before a write and retains a valid checksum across reload',async({page})=>{
 const api=await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');
 for(const invalid of ['0x'+'0'.repeat(40),'0x52908400098527886E0F7030069857D2E4169Ee7']){
  await page.getByLabel('Public analysis address').fill(invalid);await page.getByRole('button',{name:'Add address',exact:true}).click();await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('Enter a complete Ethereum address');await expect(page.locator('.savedWallet')).toHaveCount(0);expect(api.updates).toHaveLength(0);
 }
 const valid='0x52908400098527886E0F7030069857D2E4169EE7';await page.getByLabel('Public analysis address').fill(valid);await page.getByRole('button',{name:'Add address',exact:true}).click();await save(page);await page.reload({waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');await expect(page.locator('.savedWallet')).toContainText(valid.toLowerCase());expect(api.updates).toHaveLength(1);
 const input=page.getByLabel('Public analysis address');await input.fill(valid.toLowerCase());await expect(input).toHaveValue(valid.toLowerCase());await input.press('Tab');
 await page.getByRole('button',{name:'Add address',exact:true}).click();await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('already saved');await expect(page.locator('.savedWallet')).toHaveCount(1);expect(api.updates).toHaveLength(1);
});
test('profile saves remotely, failures retain drafts and account data never enters device appearance storage',async({page})=>{
 const api=await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await page.getByLabel('Display name').fill('RIVEXIS Analyst');await save(page);await page.reload({waitUntil:'domcontentloaded'});await expect(page.getByLabel('Display name')).toHaveValue('RIVEXIS Analyst');
 api.setFailure(true);await page.getByLabel('Display name').fill('Unsaved draft');await page.getByRole('button',{name:'Save changes',exact:true}).click();await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('draft is retained');await expect(page.getByLabel('Display name')).toHaveValue('Unsaved draft');await page.getByRole('button',{name:'Discard changes'}).click();await expect(page.getByLabel('Display name')).toHaveValue('RIVEXIS Analyst');
 expect(api.updates).toHaveLength(2);const storage=await page.evaluate(()=>JSON.stringify(localStorage));expect(storage).not.toContain('qa@example.invalid');expect(storage).not.toContain('RIVEXIS Analyst');expect(storage).not.toContain('walletAddresses');
});
test('appearance persists, system follows device and all public theme toggles are absent',async({page})=>{
 await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Appearance');await page.getByLabel('Theme',{exact:true}).selectOption('light');await page.getByLabel('Interface density').selectOption('compact');await save(page);await expect(page.locator('html')).toHaveAttribute('data-theme','light');await expect(page.locator('html')).toHaveAttribute('data-density','compact');
 await page.reload({waitUntil:'domcontentloaded'});await tab(page,'Appearance');await expect(page.getByLabel('Theme',{exact:true})).toHaveValue('light');await page.getByLabel('Theme',{exact:true}).selectOption('system');await save(page);await page.emulateMedia({colorScheme:'dark'});await expect(page.locator('html')).toHaveAttribute('data-theme','dark');await page.emulateMedia({colorScheme:'light'});await expect(page.locator('html')).toHaveAttribute('data-theme','light');await page.goto('/',{waitUntil:'domcontentloaded'});await expect(page.getByRole('button',{name:/Switch to .* mode/})).toHaveCount(0);
});
test('financial defaults validate exact constraints and populate only new analyses',async({page})=>{
 const api=await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Financial Preferences');await page.getByLabel('Default capital budget / USD').fill('2000.125');await page.getByLabel('Default assumed fee reserve / USD').fill('2001');await page.getByRole('button',{name:'Save changes',exact:true}).click();await expect(page.locator('.settingsFeedback [role=alert]')).toBeVisible();expect(api.updates).toHaveLength(0);
 await page.getByLabel('Default assumed fee reserve / USD').fill('20');await page.getByLabel('Default target health factor').fill('1.75');await page.getByLabel('Health factor precision').selectOption('6');await page.getByLabel('Display timezone').selectOption('UTC');await page.getByLabel('Default risk objective').selectOption('max-min');await save(page);await page.goto('/workspace/frontier',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await page.getByRole('button',{name:'Decision Intelligence',exact:false}).filter({visible:true}).click();await page.getByRole('link',{name:'Defense Planner',exact:true}).click();await expect(page.getByLabel('Capital budget / USD',{exact:true})).toHaveValue('2000.125');await expect(page.getByLabel('Target health factor',{exact:true})).toHaveValue('1.75');await expect(page.getByLabel('Assumed total fee reserve / USD',{exact:true})).toHaveValue('20');await page.getByLabel('Capital budget / USD',{exact:true}).fill('1877.1');await page.getByLabel('Account menu',{exact:true}).click();await page.getByRole('link',{name:'Settings',exact:true}).click();await tab(page,'Financial Preferences');await page.getByLabel('Default capital budget / USD').fill('3000');await save(page);await page.getByRole('button',{name:'Decision Intelligence',exact:false}).filter({visible:true}).click();await page.getByRole('link',{name:'Defense Planner',exact:true}).click();await expect(page.getByLabel('Capital budget / USD',{exact:true})).toHaveValue('1877.1');
});
test('wallet addresses are bounded preferences and browser address access never signs',async({page})=>{
 await setup(page);await page.addInitScript(({address})=>{(window as any).walletMethods=[];(window as any).ethereum={request:async({method}:{method:string})=>{(window as any).walletMethods.push(method);return method==='eth_chainId'?'0x1':[address]}}},{address});await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');await page.getByLabel('Public analysis address').fill('bad');await page.getByRole('button',{name:'Add address',exact:true}).click();await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('complete Ethereum');await page.getByRole('button',{name:'Select browser wallet address'}).click();await page.getByRole('button',{name:'Add selected analysis address'}).click();await save(page);expect(await page.evaluate(()=>(window as any).walletMethods)).toEqual(['eth_chainId','eth_requestAccounts','eth_chainId']);await page.reload({waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');await expect(page.locator('.savedWallet')).toContainText(address);await page.getByRole('button',{name:`Remove ${address}`,exact:true}).click();await save(page);await page.reload({waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');await expect(page.locator('.savedWallet')).toHaveCount(0);
});
test('sessions require explicit confirmation and unavailable notification or deletion capabilities remain truthful',async({page})=>{
 const api=await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Sessions');await page.getByRole('button',{name:'End other sessions',exact:true}).click();await page.getByRole('button',{name:'Keep other sessions'}).click();expect(api.sessionRequests).toHaveLength(0);await page.getByRole('button',{name:'End other sessions',exact:true}).click();await page.getByRole('button',{name:'Confirm end other sessions'}).click();await expect(page.getByRole('status')).toContainText('access tokens can remain valid');expect(api.sessionRequests).toEqual([{confirm:true}]);
 await tab(page,'Notifications');await expect(page.getByRole('tabpanel')).toContainText('currently unavailable');await expect(page.getByRole('checkbox')).toHaveCount(0);await tab(page,'Security');await expect(page.getByRole('link',{name:'Recover or change password'})).toHaveAttribute('href','/forgot-password');await tab(page,'Account Management');await expect(page.getByRole('link',{name:'Manage workspaces & organizations'})).toHaveAttribute('href','/workspace/settings/workspaces');await expect(page.getByRole('tabpanel')).toContainText('deletion is not currently supported');
});
test('privacy download includes the explicit export and clearing cache preserves server preferences',async({page})=>{
 await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Privacy');const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export profile & saved risk receipts'}).click();const file=await download;expect(file.suggestedFilename()).toBe('rivexis-account-export.json');const stream=await file.createReadStream();let raw='';for await(const chunk of stream!)raw+=chunk.toString();const data=JSON.parse(raw);expect(data.reports[0].id).toBe('OWN_REPORT');expect(raw).not.toMatch(/access_token|refresh_token|csrf_token/);await page.getByRole('button',{name:'Clear cached appearance'}).click();expect(await page.evaluate(()=>localStorage.getItem('rivexis_appearance'))).toBeNull();await page.reload({waitUntil:'domcontentloaded'});await tab(page,'Appearance');await expect(page.getByLabel('Theme',{exact:true})).toHaveValue('dark');
});
for(const width of [320,768,1440])test(`navigation and Settings are accessible and fit ${width}px`,async({page})=>{
 await setup(page);await page.setViewportSize({width,height:1000});await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await expect(page.locator('aside.sidebar')).toHaveCount(0);if(width<1120){await page.getByLabel('Open workspace navigation').click();await expect(page.getByRole('navigation',{name:'Mobile workspace'})).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('navigation',{name:'Mobile workspace'})).toBeHidden()}else await expect(page.getByRole('navigation',{name:'Workspace',exact:true})).toBeVisible();
 await page.getByLabel('Account menu',{exact:true}).click();await expect(page.getByRole('link',{name:'Settings',exact:true})).toBeVisible();await page.keyboard.press('Escape');await tab(page,'Accessibility');await page.getByLabel('Motion',{exact:true}).selectOption('reduce');await page.getByLabel('Contrast',{exact:true}).selectOption('high');await page.getByLabel('Text size',{exact:true}).selectOption('large');await save(page);await expect(page.locator('html')).toHaveAttribute('data-motion','reduce');await expect(page.locator('html')).toHaveAttribute('data-contrast','high');await expect(page.locator('html')).toHaveAttribute('data-text-size','large');await expect(page.getByLabel('Open workspace navigation')).toBeVisible();await page.evaluate(()=>document.fonts.ready);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);const results=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(results.violations).toEqual([]);await page.screenshot({path:`test-results/settings-accessibility-${width}.png`});
});
test('unverified account cannot render Settings controls',async({page})=>{
 await setup(page);await page.route('**/api/v1/workspaces',r=>r.fulfill({status:403,json:{detail:'Email verification required'}}));await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await expect(page.getByRole('heading',{name:'Verify your email'})).toBeVisible();await expect(page.getByLabel('Display name')).toHaveCount(0);
});

test('saved address copy, default ordering and forgetting wallet access work without signing',async({page,context,browserName})=>{
 await setup(page);
 if(browserName==='chromium')await context.grantPermissions(['clipboard-read','clipboard-write']);
 else await page.addInitScript(()=>{
  const nativeWrite=navigator.clipboard.writeText.bind(navigator.clipboard);
  Object.defineProperty(navigator.clipboard,'writeText',{value:async(value:string)=>{await nativeWrite(value);(window as any).confirmedClipboardWrite=value}});
 });
 await page.addInitScript(({address})=>{(window as any).ethereum={request:async({method}:{method:string})=>method==='eth_chainId'?'0x1':[address]}},{address});await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');
 for(const value of [address,'0x'+'2'.repeat(40)]){await page.getByLabel('Public analysis address').fill(value);await page.getByRole('button',{name:'Add address',exact:true}).click()}
 await page.getByRole('button',{name:`Copy ${address}`,exact:true}).click();
 if(browserName==='chromium')expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(address);
 else await expect.poll(()=>page.evaluate(()=>(window as any).confirmedClipboardWrite)).toBe(address);
 await page.getByRole('button',{name:'Use as default',exact:true}).click();await save(page);await page.reload({waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');await expect(page.locator('.savedWallet').first()).toContainText('0x'+'2'.repeat(40));
 await page.getByRole('button',{name:'Select browser wallet address'}).click();await expect(page.locator('.selectedWallet')).toContainText(address);await page.getByRole('button',{name:'Forget selected address'}).click();await expect(page.locator('.selectedWallet')).toHaveCount(0);await expect(page.locator('.savedWallet')).toHaveCount(2);
 await page.goto('/workspace',{waitUntil:'domcontentloaded'});await expect(page.getByLabel('Public Ethereum address',{exact:true})).toHaveValue('0x'+'2'.repeat(40));
});
test('an unsupported wallet network remains unconnected and never writes a preference',async({page})=>{
 const api=await setup(page);await page.addInitScript(()=>{(window as any).ethereum={request:async({method}:{method:string})=>method==='eth_chainId'?'0x89':['0x'+'3'.repeat(40)]}});await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Connected Wallets');await page.getByRole('button',{name:'Select browser wallet address'}).click();await expect(page.locator('.settingsFeedback [role=alert]')).toContainText('Select Ethereum');await expect(page.locator('.selectedWallet')).toHaveCount(0);expect(api.updates).toHaveLength(0);
});
test('Settings current-browser logout uses the retained CSRF controller and removes account data',async({page})=>{
 await setup(page);let ended=false;await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:!ended,email_verified:!ended}}));await page.route('**/api/v1/auth/logout',r=>{expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');ended=true;return r.fulfill({json:{status:'revoked'}})});await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Sessions');await page.getByRole('button',{name:'Log out of this browser'}).click();await expect(page).toHaveURL(/\/login$/);expect(ended).toBe(true);await expect(page.getByLabel('Display name')).toHaveCount(0);expect(await page.evaluate(()=>localStorage.getItem('rivexis_workspace_id'))).toBeNull();
});
test('Settings logout reaches the shell when the legacy event bridge is unavailable and remains pending until confirmed',async({page})=>{
 await setup(page);let ended=false,requests=0;let pending:import('@playwright/test').Route|undefined;
 await page.addInitScript(()=>{const dispatch=window.dispatchEvent.bind(window);(window as any).legacyLogoutEvents=0;window.dispatchEvent=(event:Event)=>{if(event.type==='rivexis-request-logout'){(window as any).legacyLogoutEvents++;return true}return dispatch(event)}});
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:!ended,email_verified:!ended}}));
 await page.route('**/api/v1/auth/logout',r=>{expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');requests++;pending=r});
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Sessions');await page.getByRole('button',{name:'Log out of this browser'}).click();
 await expect.poll(()=>requests).toBe(1);await expect(page.getByRole('tabpanel',{name:'Sessions'}).getByRole('button',{name:'Logging out…'})).toBeDisabled();
 expect(await page.evaluate(()=>(window as any).legacyLogoutEvents)).toBe(0);await expect(page).toHaveURL(/\/workspace\/settings$/);
 const response=page.waitForResponse('**/api/v1/auth/logout');ended=true;await pending!.fulfill({json:{status:'revoked'}});expect((await response).ok()).toBe(true);
 await expect(page).toHaveURL(/\/login$/);await expect(page.getByLabel('Display name')).toHaveCount(0);expect(await page.evaluate(()=>localStorage.getItem('rivexis_workspace_id'))).toBeNull();expect(requests).toBe(1);
});
test('Settings logout failure preserves the session and supports an explicit retry without automatic writes',async({page})=>{
 await setup(page);let requests=0,ended=false;
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:!ended,email_verified:!ended}}));
 await page.route('**/api/v1/auth/logout',r=>{requests++;expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');if(requests===1)return r.fulfill({status:503,json:{detail:'Fixture provider failure'}});ended=true;return r.fulfill({json:{status:'revoked'}})});
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Sessions');await page.getByRole('button',{name:'Log out of this browser'}).click();
 await expect(page.locator('.shellLogoutError')).toContainText('could not confirm logout');await expect(page.getByRole('button',{name:'Log out of this browser'})).toBeEnabled();
 await expect(page).toHaveURL(/\/workspace\/settings$/);expect(ended).toBe(false);expect(requests).toBe(1);expect(await page.evaluate(()=>localStorage.getItem('rivexis_workspace_id'))).toBe('SETTINGS_OWNER');
 const response=page.waitForResponse('**/api/v1/auth/logout');await page.getByRole('button',{name:'Log out of this browser'}).click();expect((await response).ok()).toBe(true);
 await expect(page).toHaveURL(/\/login$/);expect(requests).toBe(2);expect(ended).toBe(true);expect(await page.evaluate(()=>localStorage.getItem('rivexis_workspace_id'))).toBeNull();
});
test('Light Settings remain accessible and grouping changes only displayed USD totals',async({page})=>{
 await setup(page);await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await tab(page,'Appearance');await page.getByLabel('Theme',{exact:true}).selectOption('light');await save(page);await expect(page.locator('.workspaceGroupedNav .workspaceNavGroup>button').first()).toHaveCSS('color','rgb(71, 86, 86)');const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(scan.violations).toEqual([]);await tab(page,'Financial Preferences');await page.getByRole('checkbox',{name:'Group USD thousands'}).uncheck();await page.getByLabel('Health factor precision').selectOption('6');await save(page);await page.goto('/workspace',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await expect(page.getByRole('region',{name:'Observed portfolio metrics'})).toContainText('$30000.00');await expect(page.getByRole('region',{name:'Observed portfolio metrics'})).toContainText('1.333333');await expect(page.getByRole('region',{name:'Observed portfolio metrics'})).toContainText('$18000.00');
});
