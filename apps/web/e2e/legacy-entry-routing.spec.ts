import {test,expect} from './browser-test';
import {mockWorkspaceAccess} from './workspace-test-navigation';

test('legacy app entry redirects only to the canonical workspace and discards obsolete query inputs',async({request})=>{
  for(const entry of ['/app','/app?next=https%3A%2F%2Fexample.invalid','/app?view=transactions']){
    const response=await request.get(entry,{maxRedirects:0});
    expect(response.status()).toBe(307);expect(response.headers().location).toBe('/workspace');
  }
});
test('verified legacy app entry has current workspace navigation without the numbered legacy interface',async({page})=>{
  await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
  await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
  await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
  await mockWorkspaceAccess(page);await page.goto('/app',{waitUntil:'domcontentloaded'});
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByRole('navigation',{name:'Workspace',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Portfolio Intelligence',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeVisible();
  await expect(page.locator('.instrumentTabs')).toHaveCount(0);
  await expect(page.getByRole('navigation',{name:'Primary navigation',exact:true})).toHaveCount(0);
});
test('guest legacy app entry remains gated by canonical workspace authorization',async({page})=>{
  await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
  await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:false,email_verified:false}}));
  await page.route('**/api/v1/workspaces',r=>r.fulfill({status:401,json:{detail:'Authentication required'}}));
  await page.goto('/app',{waitUntil:'domcontentloaded'});await expect(page).toHaveURL(/\/workspace$/);
  await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toHaveCount(0);
});

test('educational analysis shares the approved header, focus and mobile navigation without numbered tabs',async({page})=>{
  await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
  await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
  await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
  await mockWorkspaceAccess(page);
  for(const width of [320,1440]){
    await page.setViewportSize({width,height:1000});await page.goto('/demo',{waitUntil:'domcontentloaded'});
    await expect(page.getByRole('heading',{name:'Portfolio Intelligence',exact:true})).toBeVisible();
    await expect(page.locator('.instrumentTabs,.folioNav')).toHaveCount(0);
    await expect(page.getByRole('button',{name:'Explore a hypothetical sample',exact:true})).toBeVisible();
    await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE',{exact:true})).toHaveCount(0);
    await page.getByRole('button',{name:'Explore a hypothetical sample',exact:true}).click();
    await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE',{exact:true})).toBeVisible();
    const mobile=page.getByLabel('Open workspace navigation',{exact:true});if(await mobile.isVisible())await mobile.press('Enter');
    await page.getByRole('button',{name:'Decision Intelligence',exact:true}).filter({visible:true}).press('Enter');
    await page.getByRole('link',{name:'Defense Planner',exact:true}).press('Enter');
    await expect(page).toHaveURL(/\/demo$/);
    await expect(page.getByRole('heading',{name:'Defense Frontier',exact:true})).toBeFocused();
    await expect(page.getByRole('button',{name:'Calculate alternatives ↗',exact:true})).toBeEnabled();
    await expect(page.locator('.instrumentTabs')).toHaveCount(0);
  }
});
