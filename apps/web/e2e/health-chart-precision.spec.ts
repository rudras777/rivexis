import {test,expect,type Page} from '@playwright/test';
import {sampleSnapshot} from '../../../supabase/functions/rivexis-api/defi-sample.mjs';
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';

// Controlled Aave accounting fixtures, never claimed as live protocol observations.
// With $1 debt and 80% LT, collateral USD = desired health * 5/4.
const wallet='0x'+'1'.repeat(40),instant=new Date('2026-10-18T05:00:00Z');
function fixture(raw8='124481528'){
 const s=sampleSnapshot(instant.getTime()),goal=BigInt(raw8);if(goal%4n)throw Error('Fixture must retain exact eight-decimal accounting');
 const collateral=goal*5n/4n,r=s.positions[0].reserves[0],price=BigInt(r.priceRaw);
 r.collateralRaw=((collateral*10n**18n+price-1n)/price).toString();s.positions[0].reserves[1].debtRaw='1000000';
 return {...s,sample:false,wallet,coverage:'aave',blockNumber:'28000300',blockHash:'0x'+'1'.repeat(64),observedCollateralRaw:collateral.toString(),observedDebtRaw:'100000000',observedHealthFactorRaw:(goal*10n**10n).toString()};
}
async function setup(page:Page,precision=3,grouping=true,s=fixture()){
 await page.clock.install({time:instant});await page.clock.setFixedTime(instant);
 await page.route('**/health',r=>r.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:true,email_verified:true}}));
 await page.route('**/api/v1/auth/web/csrf',r=>r.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',r=>r.fulfill({json:{items:[{id:'QA',name:'QA workspace',access_role:'OWNER'}]}}));
 await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'QA',email:'qa@example.invalid',emailVerified:true},preferences:{...DEFAULT_PREFERENCES,healthPrecision:precision,numberGrouping:grouping}}}));
 await page.route('**/api/v1/defi/snapshot',r=>r.fulfill({json:s}));await page.route('https://ethereum.publicnode.com/**',r=>r.abort('failed'));
 await page.goto('/workspace');await page.getByLabel('Public Ethereum address',{exact:true}).fill(wallet);await page.getByRole('button',{name:'Inspect wallet',exact:true}).click();await expect(page.getByText('ON-CHAIN SNAPSHOT',{exact:true})).toBeVisible();
}
const sensitivity=(page:Page)=>page.locator('figure').filter({hasText:'Aave V3 · health sensitivity to WETH'});
const headline=(page:Page)=>page.getByRole('region',{name:'Observed portfolio metrics'}).locator(':scope > div').nth(2).locator('strong');
for(const item of [
 {raw8:'99960000',precision:3,expected:'0.999'},
 {raw8:'99999996',precision:3,expected:'0.999'},
 {raw8:'100000000',precision:3,expected:'1.000'},
 {raw8:'100040000',precision:3,expected:'1.000'},
 {raw8:'124481528',precision:3,expected:'1.244'},
 {raw8:'123456788',precision:4,expected:'1.2345'},
 {raw8:'124481528',precision:4,expected:'1.2448'},
 {raw8:'124481528',precision:6,expected:'1.244815'},
 {raw8:'99999996',precision:6,expected:'0.999999'},
 {raw8:'1234567888',precision:6,expected:'12.345678'},
])test(`health precision ${item.precision} preserves raw ${item.raw8} across metric, chart and table`,async({page})=>{
 await setup(page,item.precision,true,fixture(item.raw8));await expect(headline(page)).toHaveText(item.expected);
 const chart=sensitivity(page);await expect(chart.locator('.chartReadout strong')).toHaveText(`${item.expected} HF`);
 await chart.getByText('Aave V3 · health sensitivity to WETH — data table',{exact:true}).click();
 const row=chart.getByRole('row').filter({has:page.getByRole('cell',{name:'WETH price shock 0%',exact:true})});await expect(row.getByRole('cell').nth(1)).toHaveText(item.expected);
 await expect(chart.locator('circle title').filter({hasText:'WETH price shock 0% ·'})).toHaveText(`WETH price shock 0% · ${item.expected} HF`);
});

test('frontier target label uses selected raw health precision',async({page})=>{
 await setup(page,6);await page.getByRole('button',{name:'Open Defense Frontier →',exact:true}).click();await page.getByLabel('Target health factor',{exact:true}).fill('1.234567');await page.getByRole('button',{name:'Calculate alternatives ↗',exact:true}).click();await expect(page.getByRole('group',{name:/Scatter chart/})).toContainText('Target 1.234567');
});
test('educational chart uses the saved health precision without claiming live evidence',async({page})=>{
 await setup(page,4);await page.getByRole('button',{name:'Explore a hypothetical sample',exact:true}).click();await expect(page.getByText('HYPOTHETICAL SAMPLE · NOT LIVE',{exact:true})).toBeVisible();await expect(headline(page)).toHaveText('1.3333');await expect(sensitivity(page).locator('.chartReadout strong')).toHaveText('1.3333 HF');
});
test('USD history readouts and data tables respect disabled thousands grouping',async({page})=>{
 const s={...sampleSnapshot(instant.getTime()),sample:false,wallet,coverage:'aave',blockNumber:'28000300',blockHash:'0x'+'1'.repeat(64),observedCollateralRaw:'3000000000000',observedDebtRaw:'1800000000000',observedHealthFactorRaw:'1333333333333333333'};await setup(page,3,false,s);
 const chart=page.locator('figure').filter({hasText:'Observed collateral value history'});await expect(chart.locator('.chartReadout strong')).toHaveText('$30000');await chart.getByText('Observed collateral value history — data table',{exact:true}).click();await expect(chart.getByRole('cell',{name:'30000',exact:true})).toBeVisible();await expect(chart).not.toContainText('30,000');
 await expect(page.getByRole('cell',{name:'$3000.00000000',exact:true})).toBeVisible();await expect(page.getByRole('cell',{name:'$3000.0000',exact:true})).toBeVisible();
});
test('positive sub-cent defense capital is never labeled zero in chart alternatives',async({page})=>{
 await setup(page);await page.getByRole('button',{name:'Open Defense Frontier →',exact:true}).click();await page.getByLabel('Capital budget / USD',{exact:true}).fill('0.000005');await page.getByLabel('Assumed total fee reserve / USD',{exact:true}).fill('0');await page.getByRole('button',{name:'Calculate alternatives ↗',exact:true}).click();
 const plot=page.getByRole('group',{name:/Scatter chart/}),positive=plot.getByRole('button',{name:/cost <\$0\.01/});await expect(positive.first()).toBeVisible();await positive.first().press('Enter');await expect(page.locator('.frontierSelected strong')).toHaveText('<$0.01 capital used');
 await expect(page.getByLabel('Alternative',{exact:true}).locator('option:checked')).toContainText('<$0.01');await expect(page.locator('.planComparison')).toContainText(/(?:Repay|Supply) <0\.0001/);const selected=page.locator('.alternative[data-selected="true"]');await expect(selected.getByRole('heading')).toContainText('<0.0001');await selected.getByRole('button',{name:'Preview action →',exact:true}).click();expect(Number(await page.getByLabel('Token amount',{exact:true}).inputValue())).toBeGreaterThan(0);
});
