import {test,expect,type Page} from './browser-test';
import {openWorkspaceView} from './workspace-test-navigation';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';
async function setup(page:Page){
 await page.clock.install();
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'QA',name:'QA workspace',role:'Individual',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}}));
}
test('stalled workspace access recovers to an explicit retry control',async({page})=>{
 await setup(page);let requests=0,healthy=false;
 await page.route('**/api/v1/workspaces',r=>{requests++;if(healthy)return r.fulfill({json:{items:[{id:'QA',name:'QA workspace',role:'Individual',access_role:'OWNER'}]}})});
 await page.goto('/workspace/settings',{waitUntil:'domcontentloaded'});await expect.poll(()=>requests).toBe(1);await page.clock.fastForward(35_100);
 await expect(page.getByRole('heading',{name:'Workspace could not load'})).toBeVisible();expect(requests).toBe(1);
 healthy=true;await page.getByRole('button',{name:'Retry',exact:true}).click();await expect(page.getByLabel('Display name')).toHaveValue('QA');expect(requests).toBe(2);
});
test('stalled reports stop loading and allow an explicit successful retry',async({page})=>{
 await setup(page);let requests=0,healthy=false;
 await page.route('**/api/v1/defi-reports',r=>{requests++;if(healthy)return r.fulfill({json:{items:[]}})});
 await page.goto('/workspace/reports',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Load saved reports',exact:true}).click();await expect.poll(()=>requests).toBe(1);await page.clock.fastForward(35_100);
 await expect(page.locator('.defiWorkspace [role=alert]')).toContainText('Saved reports could not load');await expect(page.getByRole('button',{name:'Load saved reports',exact:true})).toBeEnabled();expect(requests).toBe(1);
 healthy=true;await page.getByRole('button',{name:'Load saved reports',exact:true}).click();await expect.poll(()=>requests).toBe(2);await expect(page.locator('.defiWorkspace [role=alert]')).toHaveCount(0);await expect(page.getByRole('status').filter({hasText:'No saved comparisons yet.'})).toBeVisible();
});

for(const fault of ['transport','malformed-success','server-error'] as const)test(`fixture: saved comparison with ${fault} warns before retry and can be found without another write`,async({page})=>{
 await setup(page);let writes=0,saved=false;
 await page.route('**/api/v1/defi-reports',r=>{
  if(r.request().method()==='GET')return r.fulfill({json:{items:saved?[{id:'FIXTURE_ALREADY_SAVED',created_at:new Date().toISOString(),receipt:{classification:'TEST_FIXTURE'}}]:[]}});
  writes++;saved=true;expect(r.request().headers()['x-rivexis-csrf']).toBe('TEST_CSRF');
  if(fault==='transport')return r.abort('failed');
  if(fault==='malformed-success')return r.fulfill({contentType:'application/json',body:'{'});
  return r.fulfill({status:502,json:{detail:'Provider response lost'}});
 });
 await page.goto('/workspace/frontier',{waitUntil:'domcontentloaded'});
 await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();
 await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();await openWorkspaceView(page,'reports');
 await page.getByRole('button',{name:'Save comparison to account',exact:true}).click();
 await expect(page.locator('.defiWorkspace [role=alert]')).toContainText('Check the saved record');
 await expect(page.getByText(/Report saved:/)).toHaveCount(0);expect(writes).toBe(1);
 await page.getByRole('button',{name:'Load saved reports',exact:true}).click();
 await expect(page.getByText('FIXTURE_ALREADY_SAVED',{exact:true})).toBeVisible();expect(writes).toBe(1);
});
