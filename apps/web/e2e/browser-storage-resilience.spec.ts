import {expect,test,type Page} from '@playwright/test';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';

const primary={id:'STORAGE_PRIMARY',name:'Primary workspace',role:'Individual',access_role:'OWNER'};
const second={...primary,id:'STORAGE_SECOND',name:'Second workspace'};
type Fault={area:'local'|'session';operation:'access'|'getItem'|'setItem'|'removeItem';name?:'SecurityError'|'QuotaExceededError';key?:string};

async function denyStorage(page:Page,fault:Fault){
  await page.addInitScript(({area,operation,name='SecurityError',key})=>{
    const property=area==='local'?'localStorage':'sessionStorage';
    const fail=()=>{throw new DOMException('Device storage is unavailable',name)};
    if(operation==='access'){Object.defineProperty(window,property,{configurable:true,get:fail});return}
    const target=window[property],original=Storage.prototype[operation];
    Object.defineProperty(Storage.prototype,operation,{configurable:true,value:function(this:Storage,...args:string[]){
      if(this===target&&(key===undefined||args[0]===key))return fail();
      return Reflect.apply(original,this,args);
    }});
  },fault);
}

async function setup(page:Page,member=true){
  const state={member,items:[primary,second],logins:0,signups:0,logouts:0,creates:0,confirms:0,resends:0,errors:[] as string[]};
  page.on('pageerror',error=>state.errors.push(error.message));
  await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
  await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:state.member,email_verified:state.member}}));
  await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'STORAGE_TEST_CSRF'}}));
  await page.route('**/api/v1/account/settings',r=>r.fulfill({status:state.member?200:401,json:state.member?{profile:{displayName:'Storage test',email:'storage@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}:{detail:'Authentication required'}}));
  await page.route('**/api/v1/workspaces',r=>{
    if(r.request().method()==='POST'){state.creates++;state.items=[primary];return r.fulfill({json:primary})}
    return r.fulfill({status:state.member?200:401,json:state.member?{items:state.items}:{detail:'Authentication required'}});
  });
  await page.route('**/api/v1/auth/web/login',r=>{state.logins++;state.member=true;return r.fulfill({json:{csrf_token:'STORAGE_TEST_CSRF'}})});
  await page.route('**/api/v1/auth/web/signup',r=>{state.signups++;return r.fulfill({json:{verification_required:true,email_status:'accepted'}})});
  await page.route('**/api/v1/auth/logout',r=>{state.logouts++;expect(r.request().headers()['x-rivexis-csrf']).toBe('STORAGE_TEST_CSRF');state.member=false;return r.fulfill({json:{status:'revoked'}})});
  await page.route('**/api/v1/me/role',r=>r.fulfill({json:{role:'Individual'}}));
  await page.route('**/api/v1/auth/email-verification/confirm',r=>{state.confirms++;return r.fulfill({json:{status:'verified'}})});
  await page.route('**/api/v1/auth/email-verification/request',r=>{state.resends++;return r.fulfill({status:202,json:{status:'accepted'}})});
  return state;
}

async function login(page:Page){
  await page.getByLabel('Email',{exact:true}).fill('storage@example.invalid');
  await page.getByLabel('Password',{exact:true}).fill('fixture-password-only');
  await page.getByRole('button',{name:'Log in',exact:true}).click();
}

test('Overview waits for selection before fetching private destination routes',async({page,baseURL})=>{
  const state=await setup(page),premature:string[]=[],origin=new URL(baseURL??'http://127.0.0.1:3000').origin;
  page.on('request',request=>{
    const url=new URL(request.url());
    if(url.origin===origin&&['/','/workspace/overview','/workspace','/workspace/wallets','/workspace/reports'].includes(url.pathname)&&!request.isNavigationRequest())premature.push(url.pathname);
  });
  await page.goto('/workspace/overview',{waitUntil:'domcontentloaded'});
  await expect(page.locator('.workspaceSelector select')).toHaveValue(primary.id);
  // Bounded negative-request observation, not global network-idle synchronization.
  await page.waitForTimeout(1000);expect(premature).toEqual([]);
  await page.getByRole('link',{name:'Open private reports',exact:false}).click();
  await expect(page).toHaveURL(/\/workspace\/reports$/);
  await expect(page.getByRole('heading',{name:'Monitoring & Reports',exact:true})).toBeVisible();expect(state.errors).toEqual([]);
});

for(const [label,fault] of [
  ['local storage getter denied',{area:'local',operation:'access'}],
  ['workspace hint read denied',{area:'local',operation:'getItem',key:'rivexis_workspace_id'}],
  ['workspace hint write quota exceeded',{area:'local',operation:'setItem',name:'QuotaExceededError',key:'rivexis_workspace_id'}],
] as const)test(label+' preserves authorized workspace access and repeated switching',async({page})=>{
  const state=await setup(page);await denyStorage(page,fault);await page.goto('/workspace/overview');
  const selector=page.locator('.workspaceSelector select');await expect(selector).toHaveValue(primary.id);
  await selector.selectOption(second.id);await expect(selector).toHaveValue(second.id);
  await selector.selectOption(primary.id);await expect(selector).toHaveValue(primary.id);
  await page.reload();await expect(selector).toHaveValue(primary.id);expect(state.errors).toEqual([]);
});

for(const [label,fault] of [
  ['local hint removal denied',{area:'local',operation:'removeItem',key:'rivexis_workspace_id'}],
  ['session storage getter denied',{area:'session',operation:'access'}],
  ['session hint removal denied',{area:'session',operation:'removeItem',key:'rivexis_pending_destination'}],
] as const)test('confirmed logout completes when '+label,async({page})=>{
  const state=await setup(page);await denyStorage(page,fault);await page.goto('/workspace/settings');
  await expect(page.getByLabel('Display name')).toHaveValue('Storage test');
  await page.getByLabel('Account menu',{exact:true}).click();await page.getByRole('button',{name:'Log out',exact:true}).click();
  await expect(page).toHaveURL(/\/login$/);await expect(page.getByLabel('Password',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Display name')).toHaveCount(0);expect(state.logouts).toBe(1);expect(state.errors).toEqual([]);
});

test('login uses the default safe destination when session hint reads are denied',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'session',operation:'getItem'});await page.goto('/login');await login(page);
  await expect(page).toHaveURL(/\/workspace$/);await expect(page.locator('.workspaceSelector select')).toHaveValue(primary.id);
  expect(state.logins).toBe(1);expect(state.errors).toEqual([]);
});

test('successful login retains explicit feature destination when session removal is denied',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'session',operation:'removeItem'});await page.goto('/login?next=%2Fworkspace%2Ftransactions');await login(page);
  await expect(page).toHaveURL(/\/workspace\/transactions$/);await expect(page.getByRole('heading',{name:'Transaction Intelligence',exact:true})).toBeVisible();
  expect(state.logins).toBe(1);expect(state.errors).toEqual([]);
});

test('full session storage does not misreport accepted signup or grant early access',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'session',operation:'setItem',name:'QuotaExceededError'});
  await page.goto('/signup?next=%2Fworkspace%2Ffrontier');await page.getByLabel('Email',{exact:true}).fill('storage@example.invalid');
  await page.getByLabel('Password',{exact:true}).fill('fixture-password-only');await page.getByRole('button',{name:'Continue',exact:true}).click();
  await expect(page).toHaveURL(/\/verify-email\?sent=1&next=%2Fworkspace%2Ffrontier$/);
  await expect(page.getByRole('status')).toContainText('Verification email requested');await expect(page.getByLabel('Email',{exact:true})).toHaveValue('');
  expect(state.member).toBe(false);expect(state.signups).toBe(1);expect(state.errors).toEqual([]);
});

test('verification works with a manually supplied email when session storage is blocked',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'session',operation:'access'});await page.goto('/verify-email?next=%2Fworkspace%2Freports');
  await page.getByLabel('Email',{exact:true}).fill('storage@example.invalid');await page.getByRole('button',{name:'Send verification email',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('Verification request received');await page.getByLabel('Verification code').fill('123456');
  await page.getByRole('button',{name:'Verify account',exact:true}).click();await expect(page).toHaveURL(/\/login\?verified=1&next=%2Fworkspace%2Freports$/);
  expect(state.confirms).toBe(1);expect(state.resends).toBe(1);expect(state.member).toBe(false);expect(state.errors).toEqual([]);
});

test('successful verification is not reported invalid when cached email removal fails',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'session',operation:'removeItem'});await page.goto('/verify-email');
  await page.getByLabel('Email',{exact:true}).fill('storage@example.invalid');await page.getByLabel('Verification code').fill('123456');
  await page.getByRole('button',{name:'Verify account',exact:true}).click();await expect(page).toHaveURL(/\/login\?verified=1$/);
  expect(state.confirms).toBe(1);expect(state.errors).toEqual([]);
});

test('existing workspace onboarding opens without writable local hints',async({page})=>{
  const state=await setup(page);await denyStorage(page,{area:'local',operation:'setItem',name:'QuotaExceededError'});await page.goto('/onboarding?next=%2Fworkspace%2Ftransactions');
  await expect(page).toHaveURL(/\/workspace\/transactions$/);await expect(page.getByRole('heading',{name:'Transaction Intelligence',exact:true})).toBeVisible();
  expect(state.creates).toBe(0);expect(state.errors).toEqual([]);
});

test('new workspace creation completes once despite unavailable session cleanup',async({page})=>{
  const state=await setup(page);state.items=[];await denyStorage(page,{area:'session',operation:'removeItem'});await page.goto('/onboarding');
  await page.getByRole('button',{name:'Open workspace',exact:true}).click();await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.locator('.workspaceSelector select')).toHaveValue(primary.id);expect(state.creates).toBe(1);expect(state.errors).toEqual([]);
});

test('unauthenticated access with blocked storage still withholds protected content',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'local',operation:'access'});await page.goto('/workspace/frontier');
  await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();await expect(page.locator('.workspaceSelector')).toHaveCount(0);
  await expect(page.getByRole('link',{name:'Log in again',exact:true})).toHaveAttribute('href','/login?next=%2Fworkspace%2Ffrontier');expect(state.errors).toEqual([]);
});

test('failed device cleanup cannot retain financial analysis after logout and login',async({page})=>{
  const state=await setup(page);await denyStorage(page,{area:'local',operation:'removeItem'});await denyStorage(page,{area:'session',operation:'removeItem'});
  await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({json:sampleSnapshot()}));await page.goto('/workspace');
  await page.getByLabel('Public Ethereum address').fill('0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18');await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
  await expect(page.getByText('$30,000.00',{exact:true})).toBeVisible();
  await page.getByLabel('Account menu',{exact:true}).click();await page.getByRole('button',{name:'Log out',exact:true}).click();await expect(page).toHaveURL(/\/login$/);
  await login(page);await expect(page).toHaveURL(/\/workspace$/);await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeVisible();
  await expect(page.getByText('$30,000.00',{exact:true})).toHaveCount(0);expect(state.logouts).toBe(1);expect(state.logins).toBe(1);expect(state.errors).toEqual([]);
});

test('blocked browser hints do not permit external login redirects',async({page})=>{
  const state=await setup(page,false);await denyStorage(page,{area:'session',operation:'access'});await page.goto('/login?next=https%3A%2F%2Fexample.invalid%2Fphish');await login(page);
  await expect(page).toHaveURL(/\/workspace$/);await expect(page.locator('.workspaceSelector select')).toHaveValue(primary.id);
  expect(state.logins).toBe(1);expect(state.errors).toEqual([]);
});
