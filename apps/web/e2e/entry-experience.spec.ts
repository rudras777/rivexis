import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
const workspace={id:'ENTRY_TEST_WORKSPACE',name:'Entry test workspace',role:'Individual',access_role:'OWNER'};
async function setup(page:Page,member=false){
  await page.route('**/health',r=>r.fulfill({status:200,json:{status:'ready'}}));
  await page.route('**/api/v1/auth/session-status',r=>r.fulfill({status:200,json:{authenticated:member,email_verified:member}}));
  await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({status:200,json:{csrf_token:'ENTRY_TEST_CSRF'}}));
  await page.route('**/api/v1/workspaces',r=>r.fulfill({status:member?200:401,json:member?{items:[workspace]}:{detail:'Authentication required'}}));
}
test('guest feature entries preserve their destination and direct protected URLs withhold analysis',async({page})=>{
  await setup(page);await page.goto('/');
  await expect(page.getByRole('heading',{level:1})).toHaveText('See the riskbefore it becomesthe consequence.');
  await expect(page.locator('.folioNav').getByRole('link',{name:'Log in',exact:true})).toBeVisible();
  await expect(page.locator('.folioNav').getByRole('link',{name:'Sign up',exact:false})).toBeVisible();
  await page.getByRole('link',{name:'Open GasGuard',exact:false}).click();
  await expect(page).toHaveURL(/\/login\?next=%2Fworkspace%2Ftransactions$/);
  await page.goto('/app');await expect(page.getByRole('heading',{name:'Your intelligence workspace'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toHaveCount(0);
  await page.goto('/workspace/frontier');await expect(page.getByRole('heading',{name:'Session ended'})).toBeVisible();
  await expect(page.getByRole('link',{name:'Log in again'})).toHaveAttribute('href','/login?next=%2Fworkspace%2Ffrontier');
});
test('interactive educational analysis also requires a verified free account',async({page})=>{
  await setup(page);await page.goto('/demo');
  await expect(page.getByRole('heading',{name:'Your intelligence workspace'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Explore a hypothetical sample',exact:true})).toHaveCount(0);
  await expect(page.getByRole('link',{name:'Log in',exact:true})).toHaveAttribute('href','/login?next=%2Fdemo');
  await page.goto('/');await expect(page.getByRole('slider')).toHaveCount(0);
  await expect(page.locator('.signatureRiskField')).toContainText('Conceptual risk field');
});
test('returning-user login opens the allowlisted feature without exposing credentials',async({page})=>{
  await setup(page);await page.route('**/api/v1/auth/web/login',async r=>{await setup(page,true);return r.fulfill({status:200,json:{csrf_token:'ENTRY_TEST_CSRF'}})});
  await page.goto('/login?next=%2Fworkspace%2Ftransactions');await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Password',{exact:true}).fill('test-password-only');
  await page.getByRole('button',{name:'Show password'}).click();await expect(page.getByLabel('Password',{exact:true})).toHaveAttribute('type','text');await page.getByRole('button',{name:'Hide password'}).click();
  await page.getByRole('button',{name:'Log in',exact:true}).click();await expect(page).toHaveURL(/\/workspace\/transactions$/);
  await expect(page.getByRole('heading',{name:'Transaction Intelligence',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}))).not.toContain('test-password-only');
});
test('signup retains a feature destination through verification without granting an early session',async({page})=>{
  await setup(page);await page.route('**/api/v1/auth/web/signup',r=>r.fulfill({status:200,json:{verification_required:true,email_status:'accepted'}}));
  await page.route('**/api/v1/auth/email-verification/confirm',r=>r.fulfill({status:200,json:{status:'verified'}}));
  await page.goto('/signup?next=%2Fworkspace%2Ffrontier');await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Password',{exact:true}).fill('test-password-only');await page.getByRole('button',{name:'Continue',exact:true}).click();
  await expect(page).toHaveURL(/\/verify-email\?sent=1&next=%2Fworkspace%2Ffrontier$/);
  await page.getByLabel('Verification code').fill('123456');await page.getByRole('button',{name:'Verify account'}).click();
  await expect(page).toHaveURL(/\/login\?verified=1&next=%2Fworkspace%2Ffrontier$/);
  await expect(page.getByRole('status')).toContainText('Email verified');
  expect(await page.evaluate(()=>sessionStorage.getItem('rivexis_pending_destination'))).toBe('/workspace/frontier');
});
test('external and malformed destination requests fall back to the workspace',async({page})=>{
  await setup(page);await page.route('**/api/v1/auth/web/login',async r=>{await setup(page,true);return r.fulfill({status:200,json:{csrf_token:'ENTRY_TEST_CSRF'}})});
  await page.goto('/login?next=https%3A%2F%2Fexample.invalid%2Fphish');await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Password',{exact:true}).fill('test-password-only');await page.getByRole('button',{name:'Log in',exact:true}).click();
  await expect(page).toHaveURL(/\/workspace$/);
});
test('existing verified sessions open features directly and skip redundant login',async({page})=>{
  await setup(page,true);await page.goto('/');await expect(page.locator('.folioNav').getByRole('link',{name:'Open dashboard',exact:false})).toBeVisible();
  await expect(page.getByRole('link',{name:'Open GasGuard',exact:false})).toHaveAttribute('href','/workspace/transactions');
  await page.goto('/login?next=%2Fworkspace%2Ffrontier');await expect(page).toHaveURL(/\/workspace\/frontier$/);
});
test('demo context is isolated and confirmed logout clears financial memory before re-entry',async({page})=>{
  await setup(page,true);
  await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({status:200,json:sampleSnapshot()}));
  await page.route('**/api/v1/auth/logout',async r=>{await setup(page);return r.fulfill({status:200,json:{status:'revoked'}})});
  await page.route('**/api/v1/auth/web/login',async r=>{await setup(page,true);return r.fulfill({status:200,json:{csrf_token:'ENTRY_TEST_CSRF'}})});
  await page.goto('/app');await page.getByLabel('Public Ethereum address').fill('0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18');await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
  await expect(page.getByText('$30,000.00',{exact:true})).toBeVisible();
  await page.locator('.folioNav').getByRole('link',{name:'Rivexis home'}).click();await page.getByRole('link',{name:'Explore an educational demo',exact:false}).click();await expect(page).toHaveURL(/\/demo$/);await expect(page.getByRole('button',{name:'Explore a hypothetical sample'})).toBeVisible();
  await expect(page.getByText('$30,000.00',{exact:true})).toHaveCount(0);
  await page.locator('.folioNav').getByRole('link',{name:'Rivexis home'}).click();await page.locator('.folioNav').getByRole('link',{name:'Open dashboard',exact:false}).click();
  await expect(page.getByText('$30,000.00',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Log out',exact:true}).click();await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Password',{exact:true}).fill('test-password-only');await page.getByRole('button',{name:'Log in',exact:true}).click();
  await expect(page).toHaveURL(/\/workspace$/);await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeVisible();await expect(page.getByText('$30,000.00',{exact:true})).toHaveCount(0);
});
test('verified login refreshes cached guest access before opening the app',async({page})=>{
  await setup(page);await page.route('**/api/v1/auth/web/login',async r=>{await setup(page,true);return r.fulfill({status:200,json:{csrf_token:'ENTRY_TEST_CSRF'}})});
  await page.goto('/app');await page.getByRole('link',{name:'Log in',exact:true}).click();
  await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Password',{exact:true}).fill('test-password-only');await page.getByRole('button',{name:'Log in',exact:true}).click();
  await expect(page).toHaveURL(/\/app$/);await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeVisible();
});
test('a late wallet response cannot repopulate financial memory after logout',async({page})=>{
  await setup(page,true);let requested=false,release!:()=>void;const held=new Promise<void>(resolve=>{release=resolve});
  await page.route('**/api/v1/defi/snapshot',async r=>{requested=true;await held;await r.fulfill({status:200,json:sampleSnapshot()})});
  await page.route('**/api/v1/auth/logout',async r=>{await setup(page);return r.fulfill({status:200,json:{status:'revoked'}})});
  await page.route('**/api/v1/auth/web/login',async r=>{await setup(page,true);return r.fulfill({status:200,json:{csrf_token:'ENTRY_TEST_CSRF'}})});
  await page.goto('/workspace');await page.getByLabel('Public Ethereum address').fill('0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18');await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect.poll(()=>requested).toBe(true);
  await page.getByRole('button',{name:'Log out',exact:true}).click();await expect(page).toHaveURL(/\/login$/);
  const settled=page.waitForResponse('**/api/v1/defi/snapshot');release();await settled;
  await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Password',{exact:true}).fill('test-password-only');await page.getByRole('button',{name:'Log in',exact:true}).click();
  await expect(page).toHaveURL(/\/workspace$/);await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeVisible();await expect(page.getByText('$30,000.00',{exact:true})).toHaveCount(0);
});
test('landing and entry pages are accessible as a guest at mobile/desktop sizes and reduced motion',async({page})=>{
  test.setTimeout(90_000);
  await setup(page);await page.emulateMedia({reducedMotion:'reduce'});
  for(const width of [320,375,390,768,1024,1280,1440,1920,2560]){
    await page.setViewportSize({width,height:1000});await page.goto('/');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`landing overflow ${width}`).toBe(true);
    await expect(page.locator('.folioNav').getByRole('link',{name:'Sign up',exact:false})).toBeVisible();
    if(width===375){await page.getByLabel('Open navigation',{exact:true}).click();await expect(page.getByRole('navigation',{name:'Mobile navigation'})).toBeVisible();}
  }
  for(const theme of ['dark','light'])for(const path of ['/','/login','/signup','/verify-email','/forgot-password','/reset-password','/demo','/app']){
    await page.setViewportSize({width:390,height:1000});await page.addInitScript(value=>localStorage.setItem('rivexis_theme',value),theme);await page.goto(path);
    const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
    expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical'),`${theme} ${path}`).toEqual([]);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${theme} ${path}`).toBe(true);
  }
});
