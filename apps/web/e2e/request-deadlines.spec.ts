import {test,expect,type Page} from './browser-test';
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
 healthy=true;await page.getByRole('button',{name:'Load saved reports',exact:true}).click();await expect.poll(()=>requests).toBe(2);await expect(page.locator('.defiWorkspace [role=alert]')).toHaveCount(0);
});
