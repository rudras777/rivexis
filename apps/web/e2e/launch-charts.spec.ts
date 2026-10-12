import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync} from 'node:fs';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';

// Browser fixtures only. None of these responses is a current live-market claim.
const wallet='0x'+'1'.repeat(40);
function fixture(){
 const sample=sampleSnapshot();let collateral=0n,debt=0n;
 for(const p of sample.positions)for(const r of p.reserves){const unit=10n**BigInt(r.decimals),price=BigInt(r.priceRaw);if(r.collateralEnabled)collateral+=BigInt(r.collateralRaw)*price/unit;debt+=(BigInt(r.debtRaw)*price+unit-1n)/unit}
 return {...sample,observedCollateralRaw:String(collateral),observedDebtRaw:String(debt),sample:false,wallet,coverage:'aave',blockNumber:'1000',blockHash:'TEST_FIXTURE_BLOCK_1000',source:'SYNTHETIC BROWSER FIXTURE',rpcHost:'fixture.invalid'};
}
test.beforeEach(async({page})=>{
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
});
async function inspect(page:Page,s:ReturnType<typeof fixture>){
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({json:s}));
 await page.goto('/app');await page.getByLabel('Public Ethereum address').fill(s.wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();
 await expect(page.locator('.evidenceStrip')).toBeVisible();
}
const sensitivity=(page:Page)=>page.locator('figure').filter({hasText:'Aave V3 · health sensitivity to WETH'});
const history=(page:Page)=>page.locator('figure').filter({hasText:'Observed collateral value history'});

test('CH01 recorded Aave/Morpho references render separate protocol sensitivity curves',async({page})=>{
 const ref=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-portfolio-reference.json',import.meta.url),'utf8'));
 const s=ref.snapshot,delta=Math.floor(Date.now()/1000)-s.blockTimestamp;s.blockTimestamp+=delta;
 for(const p of s.positions)if(p.oracleEvidence){p.market.lastUpdateRaw=String(s.blockTimestamp);p.oracleEvidence.blockTimestamp=String(s.blockTimestamp);for(const f of p.oracleEvidence.feeds)for(const i of [2,3])f.round[i]=String(Number(f.round[i])+delta)}
 await inspect(page,s);await expect(page.getByRole('region',{name:'Position charts'}).getByRole('img')).toHaveCount(2);
 await expect(page.getByRole('img',{name:/Morpho Blue · health sensitivity to WBTC/})).toBeVisible();
 await expect(page.getByText('Aave V3: no eligible collateral reference for a sensitivity curve.',{exact:true})).toBeVisible();
 await expect(page.getByText('Sensitivity curves are explicit hypothetical price shocks', {exact:false})).toBeVisible();
});
test('CH02 debt-free position shows explanatory sensitivity state instead of fake health',async({page})=>{
 const s=fixture();s.positions[0].reserves[1].debtRaw='0';s.observedDebtRaw='0';s.observedHealthFactorRaw=null;
 await inspect(page,s);await expect(sensitivity(page)).toContainText('No finite modeled health factor');await expect(sensitivity(page).locator('svg')).toHaveCount(0);
});
test('CH03 no collateral position does not fabricate a sensitivity curve',async({page})=>{
 const s=fixture();s.positions[0].reserves[0].collateralRaw='0';s.observedCollateralRaw='0';s.observedHealthFactorRaw='0';
 await inspect(page,s);await expect(sensitivity(page)).toHaveCount(0);await expect(history(page).locator('svg circle')).toHaveCount(1);
});
test('CH04 stale position evidence withholds chart calculations and requires refresh',async({page})=>{
 const s=fixture();s.blockTimestamp-=181;await inspect(page,s);
 await expect(page.getByText('STALE SNAPSHOT',{exact:true})).toBeVisible();await expect(page.getByRole('region',{name:'Position charts'})).toHaveCount(0);
 await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();await expect(page.getByRole('button',{name:'Calculate alternatives ↗'})).toBeDisabled();
});
test('CH05 unsupported oracle model never plots a plausible risk curve',async({page})=>{
 const s=fixture();s.status='UNSUPPORTED';s.positions[0].reserves[0].oracleState='UNVALIDATED';s.warnings=['TEST FIXTURE: unvalidated oracle'];
 await inspect(page,s);await expect(page.getByText('UNSUPPORTED MODEL',{exact:true})).toBeVisible();await expect(page.getByRole('region',{name:'Position charts'})).toHaveCount(0);
});
test('CH06 educational sample is clearly hypothetical and has no observed-history series',async({page})=>{
 await page.goto('/app');await page.getByRole('button',{name:'Explore a hypothetical sample'}).click();
 await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE',{exact:true})).toBeVisible();await expect(sensitivity(page).locator('svg')).toBeVisible();await expect(sensitivity(page)).toContainText('40 modeled points');await expect(sensitivity(page)).not.toContainText('observed points');await expect(history(page)).toHaveCount(0);
 await sensitivity(page).getByText('Aave V3 · health sensitivity to WETH — data table',{exact:true}).click();await expect(sensitivity(page).getByRole('cell',{name:'WETH price shock -95%',exact:true})).toBeVisible();
});
test('CH07 debt-price stress updates sensitivity data and reset restores it',async({page})=>{
 await inspect(page,fixture());await page.getByRole('button',{name:'02Risk Scenario Lab',exact:true}).click();
 const chart=sensitivity(page);await chart.getByText('Aave V3 · health sensitivity to WETH — data table',{exact:true}).click();
 const row=chart.getByRole('row').filter({has:page.getByRole('cell',{name:'WETH price shock 0%',exact:true})});await expect(row).toContainText('1.333');
 await page.getByLabel('USDC price shock').fill('1000');await expect(row).toContainText('1.212');
 await page.getByRole('button',{name:'Reset scenario',exact:true}).click();await expect(row).toContainText('1.333');
});
test('CH08 zero-capital planner gives honest empty state without scatter points',async({page})=>{
 await inspect(page,fixture());await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();
 await page.getByLabel('Capital budget / USD',{exact:true}).fill('0');await page.getByLabel('Assumed total fee reserve / USD',{exact:true}).fill('0');
 await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();await expect(page.getByRole('heading',{name:'No alternative found that reaches your target.'})).toBeVisible();
 await expect(page.getByRole('group',{name:/Scatter chart/})).toHaveCount(0);await expect(page.getByText('No finite health factor to plot.',{exact:false})).toBeVisible();
});
test('CH09 debt-free planner retains zero-cost baseline without arbitrary numeric health',async({page})=>{
 const s=fixture();s.positions[0].reserves[1].debtRaw='0';s.observedDebtRaw='0';s.observedHealthFactorRaw=null;await inspect(page,s);
 await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
 await expect(page.getByText('No finite health factor to plot.',{exact:false})).toBeVisible();await expect(page.locator('.alternative').first()).toContainText('Keep current position');await expect(page.locator('.alternative').first()).toContainText('$0.00');
});
test('CH10 scatter alternatives support keyboard selection and preserve target labels',async({page})=>{
 await inspect(page,fixture());await page.getByRole('button',{name:'03Defense Frontier',exact:true}).click();await page.getByRole('button',{name:'Calculate alternatives ↗'}).click();
 const plot=page.getByRole('group',{name:/Scatter chart/}),second=plot.getByRole('button').nth(1);await expect(plot).toContainText('Target 1.50');
 await second.focus();await second.press('Enter');await expect(second).toHaveAttribute('aria-pressed','true');await expect(plot.getByRole('button').first()).toHaveAttribute('aria-pressed','false');
});
test('CH11 refresh deduplicates the same observed block and retains distinct-block history',async({page})=>{
 let n=0;const s=fixture();await page.route('**/api/v1/defi/snapshot',r=>{n++;const next={...s,blockNumber:n<3?'1000':'1001',blockTimestamp:s.blockTimestamp+(n<3?0:12),observedCollateralRaw:n<3?s.observedCollateralRaw:'3100000000000'};return r.fulfill({json:next})});
 await page.goto('/app');await page.getByLabel('Public Ethereum address').fill(wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(history(page).locator('svg circle')).toHaveCount(1);
 await page.getByRole('button',{name:'Refresh evidence ↻'}).click();await expect.poll(()=>n).toBe(2);await expect(history(page).locator('svg circle')).toHaveCount(1);
 await page.getByRole('button',{name:'Refresh evidence ↻'}).click();await expect(history(page).locator('svg circle')).toHaveCount(2);
 await history(page).getByText('Observed collateral value history — data table',{exact:true}).click();await expect(history(page).getByRole('cell',{name:'31,000',exact:true})).toBeVisible();
});
test('CH12 changing wallet clears previous observation history',async({page})=>{
 let n=0;const s=fixture();await page.route('**/api/v1/defi/snapshot',r=>{n++;return r.fulfill({json:{...s,wallet:r.request().postDataJSON().wallet,blockNumber:String(1000+n)}})});
 await page.goto('/app');await page.getByLabel('Public Ethereum address').fill(wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await page.getByRole('button',{name:'Refresh evidence ↻'}).click();await expect(history(page).locator('svg circle')).toHaveCount(2);
 await page.getByLabel('Public Ethereum address').fill('0x'+'2'.repeat(40));await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(history(page).locator('svg circle')).toHaveCount(1);
});
test('CH13 mobile graphs expose accessible data tables without page overflow',async({page})=>{
 await page.setViewportSize({width:375,height:900});await inspect(page,fixture());await sensitivity(page).getByText('Aave V3 · health sensitivity to WETH — data table',{exact:true}).click();
 await expect(sensitivity(page).getByRole('table')).toBeVisible();await expect(page.getByRole('img',{name:'Collateral and debt share by asset'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const scan=await new AxeBuilder({page}).include('[aria-label="Position charts"]').withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([]);
});
