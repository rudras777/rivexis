import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
test.beforeEach(async({page})=>{await page.route('**/health',r=>r.fulfill({status:200,json:{status:'ready'}}))});
test('anonymous sample connects scenarios, constrained frontier, and export',async({page})=>{
  await page.goto('/app');await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();
  await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE')).toBeVisible();
  await expect(page.getByText('$30,000.00',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'02Risk Scenario Lab',exact:true}).click();
  await page.getByLabel('WETH price shock').fill('-2000');
  await expect(page.getByText('1.333 → 1.066',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();
  await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
  await expect(page.getByRole('heading',{name:'No alternative found that reaches your target.'})).toBeVisible();
  await expect(page.getByText('MODELED ONLY',{exact:true}).first()).toBeVisible();
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export evidence',exact:true}).click();
  expect((await download).suggestedFilename()).toBe('rivexis-risk-receipt.json');
  await page.getByRole('button',{name:'04Transaction Intelligence',exact:true}).click();
  await expect(page.getByRole('button',{name:'Preview transaction ↗'})).toBeDisabled();
});
test('invalid address and unavailable provider preserve honest no-result state',async({page})=>{
  await page.goto('/app');await page.getByLabel('Public Ethereum address').fill('bad');await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
  await expect(page.locator('.defiWorkspace .error[role=alert]')).toContainText('complete Ethereum');
  await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({status:503,json:{detail:'RPC evidence unavailable'}}));
  await page.getByLabel('Public Ethereum address').fill('0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18');await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
  await expect(page.locator('.defiWorkspace .error[role=alert]')).toHaveText('RPC evidence unavailable');await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toHaveCount(0);
});

test('portfolio shows exact oracle units and never hides a positive dust balance as zero',async({page})=>{
  const fixture=sampleSnapshot();fixture.wallet='0x'+'1'.repeat(40);fixture.positions[0].reserves[0].collateralRaw='1';fixture.positions[0].reserves[1].priceRaw='99991234';
  await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({status:200,json:{...fixture,sample:false}}));
  await page.setViewportSize({width:375,height:900});await page.goto('/app');await page.getByLabel('Public Ethereum address').fill(fixture.wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
  await expect(page.getByRole('cell',{name:'$0.99991234',exact:true})).toBeVisible();
  await expect(page.getByRole('cell',{name:'<0.00000001',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('responsive dark/light product surfaces have no page overflow or serious axe findings',async({page})=>{
  for(const width of [320,375,390,768,1024,1280,1440,1920]){
    await page.setViewportSize({width,height:1000});await page.goto('/');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`home overflow ${width}`).toBe(true);
    await page.goto('/app');await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();
    await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`app overflow ${width}`).toBe(true);
  }
  for(const path of ['/','/app','/login','/signup','/forgot-password','/verify-email','/methodology']){
    await page.goto(path);const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
    expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical'),path).toEqual([]);
  }
  await page.goto('/app');await page.getByRole('button',{name:'Switch to light mode'}).click();await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  const light=await new AxeBuilder({page}).withTags(['wcag2aa','wcag22aa']).analyze();expect(light.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([]);
});
test('obsolete public tools redirect to the unified product',async({page})=>{
  await page.goto('/blockchain-intelligence');await expect(page).toHaveURL(/\/gasguard$/);
  await page.goto('/crypto-finance');await expect(page).toHaveURL(/\/liquidationguard$/);
});
test('optional browser monitoring stops after five checks and never runs for a sample',async({page})=>{
  await page.clock.install();let requests=0;
  await page.route('**/api/v1/defi/snapshot',route=>{requests++;const fixture=sampleSnapshot();return route.fulfill({status:200,json:{...fixture,sample:false,wallet:'0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18',blockNumber:String(1000+requests),blockHash:'TEST_FIXTURE'}})});
  await page.goto('/app');await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await page.getByRole('button',{name:'05Monitoring & Reports',exact:true}).click();
  await expect(page.getByRole('button',{name:'Start five bounded checks'})).toBeDisabled();
  await page.getByLabel('Public Ethereum address').fill('0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18');await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
  await expect.poll(()=>requests).toBe(1);await page.getByRole('button',{name:'Start five bounded checks'}).click();await expect.poll(()=>requests).toBe(2);
  for(let n=3;n<=6;n++){await page.clock.fastForward(120000);await expect.poll(()=>requests).toBe(n)}
  await expect(page.getByText('Five checks complete. Monitoring stopped; restart explicitly if needed.')).toBeVisible();
  await page.clock.fastForward(240000);expect(requests).toBe(6);
});
test('an already-met target ranks a zero-cost current-state alternative first',async({page})=>{
  await page.goto('/app');await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();
  await page.getByLabel('Target health factor',{exact:true}).fill('1.2');await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
  const best=page.locator('.alternative').first();await expect(best).toContainText('Keep current position (no transaction)');await expect(best).toContainText('$0.00');
  await expect(best.getByRole('button',{name:'No transaction required'})).toBeDisabled();
});
