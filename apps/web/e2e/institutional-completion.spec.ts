import {test,expect,type Page} from '@playwright/test';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
import {frontier,format} from '../../../supabase/functions/rivexis-api/defi-unified-model.mjs';
import {readFileSync} from 'node:fs';
const wallet='0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18';
function fixture(now=Date.now()){return {...sampleSnapshot(now),sample:false,wallet,blockNumber:'18001',blockHash:'0x'+'1'.repeat(64)};}
async function setup(page:Page){
 await page.route('**/health',r=>r.fulfill({status:200,json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({status:200,json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({status:200,json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({status:200,json:{items:[{id:'COMPLETION_WORKSPACE',name:'Test workspace',role:'Individual',access_role:'OWNER'}]}}));
}
test('liquidation illustration matches independent example arithmetic and aligns labels to their health-factor markers',async({page})=>{
 await setup(page);
 for(const width of [320,390,1440]){
  await page.setViewportSize({width,height:1000});await page.goto('/');
  const figure=page.locator('.thresholdPlate');
  // Independent reference: 10*3000*.8/18000; after shock, 10*2400*.8/18000.
  await expect(figure.locator('.thresholdHeadline strong')).toHaveText(['1.333','1.066']);
  await expect(figure).toContainText('NOT LIVE DATA');
  await expect(figure).toContainText('Hypothetical inputs; no live oracle or execution evidence');
  await expect(figure.locator('.healthAxisRange span')).toHaveText(['0.800','1.500']);
  const positions=await figure.locator('.healthAxisTrack').evaluate(track=>{
   const box=track.getBoundingClientRect();
   return ['Boundary','Baseline','Scenario'].map(name=>{
    const mark=track.querySelector('.healthAxis'+name)!,label=mark.querySelector('span')!;
    const m=mark.getBoundingClientRect(),l=label.getBoundingClientRect();
    return {name,fraction:(m.x-box.x)/box.width,labelCenterError:Math.abs((l.x+l.width/2)-(m.x+m.width/2)),labelLeft:l.x,labelRight:l.right};
   });
  });
  for(const [index,expected] of [2/7,16/21,8/21].entries()){
   expect(positions[index].fraction).toBeCloseTo(expected,3);
   expect(positions[index].labelCenterError).toBeLessThan(1);
   expect(positions[index].labelLeft).toBeGreaterThanOrEqual(0);expect(positions[index].labelRight).toBeLessThanOrEqual(width);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 }
});

test('planner selection, supported preview and route return retain the original plan',async({page})=>{
 await setup(page);const snapshot=fixture();
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({status:200,json:snapshot}));
 await page.route('**/api/v1/defi/transaction',r=>r.fulfill({status:200,json:{status:'PREVIEW_ONLY',simulation:'SUCCEEDED_AT_BLOCK',blockNumber:'19002',blockHash:'0x'+'2'.repeat(64),nonceAtBlock:7,before:{healthFactorRaw:'1333333333333333333'},after:{healthFactorRaw:'1500000000000000000'},gasRaw:'100000',feeReserveWei:'100000000000000',blockers:[],warnings:[]}}));
 await page.goto('/workspace/frontier');await page.getByLabel('Public Ethereum address',{exact:true}).fill(wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
 await expect(page.getByRole('region',{name:'Selected defense plan comparison'})).toBeVisible();
 await page.getByLabel('Alternative',{exact:true}).selectOption('1');await expect(page.getByRole('heading',{name:'Inspect alternative 2'})).toBeVisible();
 await page.getByRole('button',{name:/Select alternative 1:/}).press('Enter');await expect(page.getByRole('heading',{name:'Inspect alternative 1'})).toBeVisible();
 // Opening a different card must also select that alternative.
 await page.locator('.alternative').nth(1).getByRole('button',{name:'Preview action →'}).click();await expect(page).toHaveURL(/\/workspace\/transactions$/);
 await expect(page.getByLabel('Token amount',{exact:true})).not.toHaveValue('');await page.getByRole('button',{name:'Preview transaction ↗'}).click();
 await expect(page.getByText('Simulation block 19002 · Observed nonce 7')).toBeVisible();await expect(page.getByText('Block 18001',{exact:false})).toBeVisible();
 await page.getByRole('link',{name:/^(03 )?Defense Frontier$/,exact:true}).click();await expect(page.getByRole('heading',{name:'Inspect alternative 2'})).toBeVisible();
 await page.getByLabel('Capital budget / USD',{exact:true}).fill('100');await expect(page.getByRole('region',{name:'Selected defense plan comparison'})).toHaveCount(0);
});
test('private saved comparison reopens as historical and requires refresh for new work',async({page})=>{
 await setup(page);const snapshot=fixture(Date.now()-600000),constraints={budget:'3000',target:'1.5',gasReserve:'25',objective:'target',shocks:{}};
 await page.route('**/api/v1/defi-reports',r=>r.fulfill({status:200,json:{items:[{id:'OWNER_ARCHIVE',created_at:new Date().toISOString(),receipt:{snapshot,constraints,result:frontier(snapshot,constraints,snapshot.blockTimestamp*1000)}}]}}));
 await page.goto('/workspace/reports');await page.getByRole('button',{name:'Load saved reports'}).click();await page.getByRole('button',{name:'Open comparison →'}).click();
 await expect(page).toHaveURL(/\/workspace\/frontier$/);await expect(page.getByText('HISTORICAL COMPARISON · REFRESH REQUIRED')).toBeVisible();
 await expect(page.getByRole('region',{name:'Selected defense plan comparison'})).toBeVisible();await expect(page.getByRole('button',{name:'Calculate alternatives ↗'})).toBeDisabled();await expect(page.locator('.alternative').first().getByRole('button',{name:'Preview action →'})).toBeDisabled();
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({status:200,json:fixture()}));await page.getByRole('button',{name:'Refresh evidence ↻'}).click();await expect(page.getByText('HISTORICAL COMPARISON · REFRESH REQUIRED')).toHaveCount(0);await expect(page.getByRole('button',{name:'Calculate alternatives ↗'})).toBeEnabled();
});
test('unverified identities receive a usable verification route before workspace content',async({page})=>{
 await setup(page);await page.route('**/api/v1/workspaces',r=>r.fulfill({status:403,json:{detail:'Email verification is required before analysis or reports'}}));
 await page.goto('/workspace/frontier');await expect(page.getByRole('heading',{name:'Verify your email'})).toBeVisible();await expect(page.getByRole('link',{name:'Verify email',exact:true})).toHaveAttribute('href','/verify-email?next=%2Fworkspace%2Ffrontier');await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toHaveCount(0);
});
test('landing depth and cursor effects are bounded, optional and never replace the native pointer',async({page})=>{
 await setup(page);await page.setViewportSize({width:1440,height:1000});await page.goto('/');
 await expect(page.locator('.heroFolioWrap')).toHaveCount(0);await expect(page.getByRole('slider')).toHaveCount(0);
 const art=page.locator('.signatureRiskField');await expect(art).toBeVisible();const box=(await art.boundingBox())!;await page.mouse.move(box.x+box.width*.8,box.y+box.height*.5);
 await expect.poll(()=>art.evaluate(e=>e.style.getPropertyValue('--field-x'))).not.toBe('');
 await page.emulateMedia({reducedMotion:'reduce'});await page.mouse.move(box.x+box.width*.2,box.y+box.height*.5);await expect(page.locator('.precisionPointer')).toBeHidden();
 expect(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');expect(await page.evaluate(()=>getComputedStyle(document.body).cursor)).not.toBe('none');
});

test('a verified OTP response opens the original feature with a refreshed account cache',async({page})=>{
 await setup(page);await page.route('**/api/v1/auth/session-status',r=>r.fulfill({status:200,json:{authenticated:false,email_verified:false}}));
 await page.route('**/api/v1/auth/email-verification/confirm',async r=>{await page.route('**/api/v1/auth/session-status',v=>v.fulfill({status:200,json:{authenticated:true,email_verified:true}}));await r.fulfill({status:200,json:{status:'verified',authenticated:true,csrf_token:'TEST_CSRF'}})});
 await page.goto('/verify-email?next=%2Fworkspace%2Ffrontier');await page.getByLabel('Email',{exact:true}).fill('qa@example.invalid');await page.getByLabel('Verification code').fill('test-only-code');await page.getByRole('button',{name:'Verify account'}).click();
 await expect(page).toHaveURL(/\/workspace\/frontier$/);await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toBeVisible();
});

// Deliberately hypothetical balances on recorded protocol structures. The canonical
// planner computes the alternatives; no alternative list or financial result is mocked.
function multiActionFixture(){
 const s=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-portfolio-reference.json',import.meta.url),'utf8')).snapshot;
 const delta=Math.floor(Date.now()/1000)-s.blockTimestamp;s.blockTimestamp+=delta;
 for(const p of s.positions)if(p.oracleEvidence){p.market.lastUpdateRaw=String(s.blockTimestamp);p.oracleEvidence.blockTimestamp=String(s.blockTimestamp);for(const f of p.oracleEvidence.feeds)for(const i of [2,3])f.round[i]=String(Number(f.round[i])+delta);}
 s.sample=false;s.nativeBalanceRaw='100000000000000000000';
 const a=s.positions.find((p:{protocol:string})=>p.protocol==='Aave V3'),m=s.positions.find((p:{protocol:string})=>p.protocol==='Morpho Blue'),loan=structuredClone(m.reserves.find((r:{symbol:string})=>r.symbol==='USDC'));
 loan.debtRaw='25000000000';a.reserves.push(loan);a.reserves[0].collateralRaw='10000000000000000000';
 for(const p of s.positions)for(const r of p.reserves)r.walletRaw=r.symbol==='USDC'?'1000000000000':r.symbol==='WBTC'?'1000000000':'10000000000000000000';
 return s;
}
const multiConstraints={budget:'1000000',gasReserve:'10',target:'1.50',objective:'max-min',shocks:{}};
for(const width of [375,1440])test(`multi-position planner hands each action to GasGuard independently at ${width}px`,async({page})=>{
 await setup(page);await page.setViewportSize({width,height:1000});const snapshot=multiActionFixture(),result=frontier(snapshot,multiConstraints);
 expect(result.alternatives[0].actions).toHaveLength(2);expect(result.alternatives[0].actions[1].sharesRaw).toBeTruthy();
 const requests:Record<string,unknown>[]=[];
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({status:200,json:snapshot}));
 await page.route('**/api/v1/defi/transaction',r=>{requests.push(r.request().postDataJSON());return r.fulfill({status:200,json:{status:'PREVIEW_ONLY',simulation:'SUCCEEDED_AT_BLOCK',blockNumber:'19002',nonceAtBlock:7,before:{healthFactorRaw:'1333333333333333333'},after:{healthFactorRaw:'1500000000000000000'},gasRaw:'100000',feeReserveWei:'100000000000000',blockers:[],warnings:[]}})});
 await page.goto('/workspace/frontier');await page.getByLabel('Protocol coverage').selectOption('combined');await page.getByLabel('Public Ethereum address',{exact:true}).fill(snapshot.wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
 await page.getByLabel('Capital budget / USD',{exact:true}).fill(multiConstraints.budget);await page.getByLabel('Assumed total fee reserve / USD',{exact:true}).fill(multiConstraints.gasReserve);await page.getByRole('combobox',{name:/^Risk objective/}).selectOption('max-min');await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
 await expect(page.locator('.alternative')).toHaveCount(result.alternatives.length);
 const card=page.locator('.alternative').first();await expect(card).toContainText('Independent previews; combined execution is not simulated.');await expect(card.getByRole('button')).toHaveCount(2);await card.screenshot({path:`test-results/frontier-independent-${width}.png`});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 for(const [index,action] of result.alternatives[0].actions.entries()){
  await page.getByLabel('Alternative',{exact:true}).selectOption('1'); // Deliberately start from a different strategy.
  await card.getByRole('button').nth(index).click();await expect(page).toHaveURL(/\/workspace\/transactions$/);
  await expect(page.getByLabel('Transaction position')).toHaveValue(action.positionId);await expect(page.getByLabel('Asset',{exact:true})).toHaveValue(action.asset);await expect(page.getByLabel('Action',{exact:true})).toHaveValue(action.kind);
  const amount=format(action.amountRaw,action.decimals,action.decimals);await expect(page.getByLabel('Token amount',{exact:true})).toHaveValue(amount);
  await expect(page.getByText('Each preview reads fresh chain state and excludes other planned actions; it does not validate combined execution.',{exact:false})).toBeVisible();
  expect(requests).toHaveLength(index); // Selecting an action never calls RPC or executes a transaction.
  await page.getByRole('button',{name:'Preview transaction ↗'}).click();await expect(page.getByText('Simulation block 19002 · Observed nonce 7')).toBeVisible();
  expect(requests[index]).toEqual({wallet:snapshot.wallet,coverage:'combined',positionId:action.positionId,asset:action.asset,kind:action.kind,amount,...(action.sharesRaw?{sharesRaw:action.sharesRaw}:{})});
  await page.getByRole('link',{name:/^(03 )?Defense Frontier$/,exact:true}).click();await expect(page.getByRole('heading',{name:'Inspect alternative 1'})).toBeVisible();await expect(page.getByLabel('Capital budget / USD',{exact:true})).toHaveValue(multiConstraints.budget);await expect(page.locator('.alternative')).toHaveCount(result.alternatives.length);
 }
});

test('historical multi-action comparisons keep every individual preview disabled',async({page})=>{
 await setup(page);const snapshot=multiActionFixture();
 await page.route('**/api/v1/defi-reports',r=>r.fulfill({status:200,json:{items:[{id:'MULTI_ARCHIVE',created_at:new Date().toISOString(),receipt:{snapshot,constraints:multiConstraints}}]}}));
 let transactionRequests=0;await page.route('**/api/v1/defi/transaction',r=>{transactionRequests++;return r.abort()});
 await page.goto('/workspace/reports');await page.getByRole('button',{name:'Load saved reports'}).click();await page.getByRole('button',{name:'Open comparison →'}).click();
 await expect(page.getByText('HISTORICAL COMPARISON · REFRESH REQUIRED')).toBeVisible();const buttons=page.locator('.alternative').first().getByRole('button');await expect(buttons).toHaveCount(2);await expect(buttons.nth(0)).toBeDisabled();await expect(buttons.nth(1)).toBeDisabled();expect(transactionRequests).toBe(0);
});
