import {expect,type Page} from './browser-test';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';

// Explicit local fixture support, invoked only by already authenticated scenarios.
// This does not mock sessions or change production/public checks.
export async function mockWorkspaceAccess(page:Page,theme:'dark'|'light'='dark'){
  await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'CANONICAL_QA',name:'Canonical QA workspace',role:'Individual',access_role:'OWNER'}]}}));
  await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:{...DEFAULT_PREFERENCES,theme}}}));
}

export async function openWorkspaceView(page:Page,view:'portfolio'|'scenarios'|'frontier'|'transactions'|'reports'){
  const educational=new URL(page.url()).pathname==='/demo';
  const destinations={portfolio:['Risk Intelligence','LiquidationGuard','/workspace'],scenarios:['Risk Intelligence','Stress Testing','/workspace/scenarios'],frontier:['Decision Intelligence','Defense Planner','/workspace/frontier'],transactions:['Transaction Intelligence','GasGuard','/workspace/transactions'],reports:['Research & Monitoring','Monitoring & Reports','/workspace/reports']} as const;
  const [category,label,path]=destinations[view];
  const mobile=page.getByLabel('Open workspace navigation',{exact:true});
  if(await mobile.isVisible()&&!await page.getByRole('navigation',{name:'Mobile workspace',exact:true}).isVisible())await mobile.click();
  await page.getByRole('button',{name:category,exact:true}).filter({visible:true}).click();
  await page.getByRole('link',{name:label,exact:true}).click();
  if(educational){
    const headings={portfolio:'Portfolio Intelligence',scenarios:'Risk Scenario Lab',frontier:'Defense Frontier',transactions:'Transaction Intelligence',reports:'Monitoring & Reports'};
    await expect(page).toHaveURL(/\/demo$/);
    await expect(page.getByRole('heading',{level:1,name:headings[view],exact:true})).toBeVisible();
  }else await expect(page).toHaveURL(new RegExp(path+'$'));
}
