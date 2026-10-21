import {test,expect as baseExpect,type Page} from './browser-test';
// Initial canonical/history reads are bounded at25s; do not assert completion at5s.
const expect=baseExpect.configure({timeout:30000});
test.setTimeout(45000);
import {DEFAULT_PREFERENCES} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';

const endpoint='https://ethereum.publicnode.com';
const head=30_000_000;
const hex=(number:number)=>`0x${number.toString(16)}`;
const hash=(number:number)=>`0x${BigInt(number).toString(16).padStart(64,'0')}`;
const word=(number:number|bigint)=>BigInt(number).toString(16).padStart(64,'0');
type RpcCall={id:number;method:string;params:any[]};
type Mode='success'|'stale quote'|'negative quote'|'wrong chain'|'offline'|'rate limited'|'reorg'|'empty fees'|'archive unavailable'|'history gaps'|'future quote'|'ETH feed unavailable';

async function account(page:Page,authenticated=true){
 await page.route('**/health',route=>route.fulfill({json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',route=>route.fulfill({json:{authenticated,email_verified:authenticated}}));
 await page.route('**/api/v1/auth/web/csrf',route=>route.fulfill({json:{csrf_token:'TEST_CSRF'}}));
 await page.route('**/api/v1/workspaces',route=>route.fulfill({status:authenticated?200:401,json:authenticated?{items:[{id:'OWNER',name:'Primary workspace',role:'Individual',access_role:'OWNER'}]}:{error:{code:'AUTHENTICATION_REQUIRED',message:'Sign in'}}}));
 await page.route('**/api/v1/account/settings',route=>route.fulfill({status:authenticated?200:401,json:authenticated?{profile:{displayName:'Analyst',email:'qa@example.invalid',emailVerified:true},preferences:DEFAULT_PREFERENCES}:{error:{code:'AUTHENTICATION_REQUIRED',message:'Sign in'}}}));
}

test('market quote labels respect the saved USD grouping preference',async({page})=>{
 await account(page);await page.route('**/api/v1/account/settings',r=>r.fulfill({json:{profile:{displayName:'Analyst',email:'qa@example.invalid',emailVerified:true},preferences:{...DEFAULT_PREFERENCES,numberGrouping:false}}}));await rpc(page);await page.goto('/workspace/overview',{waitUntil:'domcontentloaded'});await expect(page.locator('.marketPrice')).toHaveText(['$3000.00','$90000.00']);
});

/** RPC fixtures live only at the network boundary; no product quote or success state is injected. */
async function rpc(page:Page,mode:Mode='success'){
 const state={mode,reads:0,batches:0,number:head,time:0,chains:0,archiveCalls:0};
 await page.route(`${endpoint}/**`,async route=>{
  const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type','Access-Control-Allow-Methods':'POST, OPTIONS'};
  if(route.request().method()==='OPTIONS'){await route.fulfill({status:204,headers});return}
  state.batches++;
  if(state.mode==='offline'){await route.abort('failed');return}
  if(state.mode==='rate limited'){await route.fulfill({status:429,body:'Rate limited',headers});return}
  const calls=route.request().postDataJSON() as RpcCall[];
  expect(calls.length).toBeLessThanOrEqual(4);
  // RPC fixtures and the reader share the browser clock when time is advanced.
  const latestTime=calls.some(call=>call.method==='eth_getBlockByNumber'&&call.params[0]==='latest')?Math.floor(await page.evaluate(()=>Date.now())/1000):state.time;
  const results=calls.map(call=>{
   let result:any;
   if(call.method==='eth_chainId'){state.chains++;result=state.mode==='wrong chain'?'0x89':'0x1'}
   else if(call.method==='eth_getBlockByNumber'){
    if(call.params[0]==='latest'){state.reads++;state.number=head+state.reads-1;state.time=latestTime;state.chains=1}
    const number=call.params[0]==='latest'?state.number:Number(BigInt(call.params[0]));
    result={number:hex(number),hash:hash(number),parentHash:hash(number-1),timestamp:hex(state.time-(state.number-number)*12),baseFeePerGas:'0x3b9aca00'};
    if(state.mode==='reorg'&&state.chains>=2&&number===state.number)result.hash=hash(number+100);
   }else if(call.method==='eth_feeHistory'){
    result={oldestBlock:hex(state.number-3),baseFeePerGas:Array(5).fill('0x3b9aca00'),gasUsedRatio:Array(4).fill(.5)};
    if(state.mode==='empty fees')result={oldestBlock:hex(state.number),baseFeePerGas:[],gasUsedRatio:[]};
   }else if(call.method==='eth_call'){
    const [transaction,pinned]=call.params;
    expect(pinned.requireCanonical).toBe(true);
    const number=Number(BigInt(pinned.blockHash));
    const archived=number<state.number;
    if(archived)state.archiveCalls++;
    if(state.mode==='ETH feed unavailable'&&transaction.to==='0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419')return {jsonrpc:'2.0',id:call.id,error:{code:-32000,message:'ETH feed temporarily unavailable'}};
    if(archived&&(state.mode==='archive unavailable'||state.mode==='history gaps'))return {jsonrpc:'2.0',id:call.id,error:{code:-32000,message:'Archive state unavailable'}};
    if(transaction.data==='0x313ce567')result=`0x${word(8)}`;
    else{
     const isEth=transaction.to==='0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419';
     expect(['0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419','0xf4030086522a5beea4988f8ca5b36dbc97bee88c']).toContain(transaction.to);
     const roundId=transaction.data.startsWith('0x9a6fc8f5')?BigInt(`0x${transaction.data.slice(10)}`):10n;
     let timestamp=state.time-(state.number-number)*12-60-Number(10n-roundId)*(state.mode==='history gaps'?10800:600);
     if(state.mode==='stale quote')timestamp=state.time-7200;
     if(state.mode==='future quote')timestamp=state.time+60;
     let answer=isEth?300000000000n:9000000000000n;
     if(state.mode==='negative quote'&&isEth)answer=(1n<<256n)-1n;
     result=`0x${[roundId,answer,BigInt(timestamp-1),BigInt(timestamp),roundId].map(word).join('')}`;
    }
   }else throw new Error(`Unsupported fixture method ${call.method}`);
   return {jsonrpc:'2.0',id:call.id,result};
  }).reverse();
  await route.fulfill({json:results,headers});
 });
 return state;
}
const panel=(page:Page)=>page.getByRole('region',{name:'Live on-chain market context'});
async function open(page:Page,mode:Mode='success',path='/workspace/overview'){
 await account(page);const state=await rpc(page,mode);await page.goto(path,{waitUntil:'domcontentloaded'});await expect(panel(page)).toBeVisible();return state;
}

test('market: validated quotes, real-shape fee history and accessible exact-value tables',async({page})=>{
 const state=await open(page);await expect(panel(page)).toContainText('Fresh block observation');
 await expect(panel(page)).toContainText('$3,000');await expect(panel(page)).toContainText('$90,000');
 await expect(panel(page).getByRole('img',{name:'Ethereum observed base fee history'})).toBeVisible();
 await panel(page).getByText('Ethereum observed base fee history — data table',{exact:true}).click();
 await expect(panel(page).locator('table').last().locator('tbody tr')).toHaveCount(4);
 await expect(panel(page).locator('table').last()).toContainText('UTC');expect(state.reads).toBe(1);
});
test('market: stale oracle is labeled separately from fresh block',async({page})=>{
 await open(page,'stale quote');await expect(panel(page)).toContainText('Fresh block observation');await expect(panel(page)).toContainText('Stale oracle round');
});
test('market: negative oracle quote is unavailable without hiding valid second feed',async({page})=>{
 await open(page,'negative quote');await expect(panel(page)).toContainText('No validated quote');await expect(panel(page)).toContainText('$90,000');await expect(panel(page)).not.toContainText('$-');
});
test('market: future oracle timestamps fail validation',async({page})=>{
 await open(page,'future quote');await expect(panel(page)).toContainText('Invalid or incomplete oracle round');await expect(panel(page)).not.toContainText('$3,000');
});
test('market: wrong provider chain fails closed with no chart',async({page})=>{
 await open(page,'wrong chain');await expect(panel(page)).toContainText('not Ethereum mainnet');await expect(panel(page).getByRole('img')).toHaveCount(0);
});
test('market: provider transport failure shows truthful unavailable state',async({page})=>{
 await open(page,'offline');await expect(panel(page)).toContainText('Provider unavailable');await expect(panel(page)).toContainText('No fabricated market series');await expect(panel(page).getByRole('img')).toHaveCount(0);
});
test('market: provider HTTP rate limiting is surfaced without success',async({page})=>{
 await open(page,'rate limited');await expect(panel(page)).toContainText('HTTP 429');await expect(panel(page)).not.toContainText('Fresh block observation');
});
test('market: disconnection retains evidence with warning and recovers on explicit retry',async({page})=>{
 await page.clock.install();const state=await open(page);await expect(panel(page)).toContainText('$3,000');
 state.mode='offline';await page.clock.fastForward(61000);await expect(panel(page)).toContainText('Provider unavailable; retained observations may be stale');await expect(panel(page)).toContainText('$3,000');
 state.mode='success';await panel(page).getByRole('button',{name:'Refresh market context',exact:true}).click();await expect(panel(page)).toContainText(`Block ${head+1}`);await expect(panel(page)).not.toContainText('Provider unavailable');
});
test('market: final observed-block reorg rejects all rendered results',async({page})=>{
 await open(page,'reorg');await expect(panel(page)).toContainText('changed during read');await expect(panel(page).getByRole('img')).toHaveCount(0);
});
test('market: empty fee history remains unavailable while valid quotes work',async({page})=>{
 await open(page,'empty fees');await expect(panel(page)).toContainText('$3,000');await expect(panel(page)).toContainText('Fee history unavailable');await expect(panel(page).getByRole('img',{name:'Ethereum observed base fee history'})).toHaveCount(0);
});
test('market: archive failure obtains actual-shape previous rounds with explicit coverage limits',async({page})=>{
 await open(page,'archive unavailable');await expect(panel(page)).toContainText('$3,000');await expect(panel(page)).toContainText('7 observed points');
 await panel(page).getByText('Market observation provenance',{exact:true}).click();await expect(panel(page)).toContainText('Provider cannot serve this observation');await expect(panel(page)).toContainText('No fixed 24-hour coverage is promised');
});
test('market: missing time intervals break chart lines rather than fill gaps',async({page})=>{
 await open(page,'history gaps');await expect(panel(page)).toContainText('Fresh block observation');
 const chart=panel(page).getByRole('img',{name:'ETH / USD · observed oracle history'});
 await expect(chart.locator('circle')).toHaveCount(7);await expect(chart.locator('polyline')).toHaveCount(7);
});
test('market: repeated manual refresh is bounded and later block advance updates evidence',async({page})=>{
 await page.clock.install();const state=await open(page);await expect(panel(page)).toContainText(`Block ${head}`);
 await panel(page).getByRole('button',{name:'Refresh market context',exact:true}).click();await expect(panel(page)).toContainText('Wait 15 seconds');expect(state.reads).toBe(1);
 await page.clock.fastForward(16000);await panel(page).getByRole('button',{name:'Refresh market context',exact:true}).click();await expect(panel(page)).toContainText(`Block ${head+1}`);expect(state.reads).toBe(2);
});

test('market: a recovered missing feed backfills history after bounded delay without repeated archive polling',async({page})=>{
 await page.clock.install();const state=await open(page,'ETH feed unavailable');await expect(panel(page)).toContainText('No validated quote');
 const archiveCalls=state.archiveCalls;state.mode='success';await page.clock.fastForward(60001);await expect(panel(page).locator('.marketQuoteStatus')).toContainText(['Fresh oracle round','Fresh oracle round']);expect(state.archiveCalls).toBe(archiveCalls);
 await page.clock.fastForward(240001);
 await expect.poll(()=>state.archiveCalls).toBeGreaterThan(archiveCalls);
 const chart=panel(page).getByRole('img',{name:'ETH / USD · observed oracle history'});await expect.poll(()=>chart.locator('circle').count()).toBeGreaterThanOrEqual(7);
});
test('market: hidden-tab polling pauses and resumes after becoming visible',async({page})=>{
 await page.clock.install();await page.addInitScript(()=>{(window as any).launchHidden=false;Object.defineProperty(document,'hidden',{configurable:true,get:()=>(window as any).launchHidden})});
 const state=await open(page);await expect(panel(page)).toContainText('Fresh block observation');
 await page.evaluate(()=>{(window as any).launchHidden=true;document.dispatchEvent(new Event('visibilitychange'))});await expect(panel(page)).toContainText('Paused while this tab is hidden');
 const reads=state.reads;await page.clock.fastForward(125000);expect(state.reads).toBe(reads);await expect(panel(page).locator('.marketQuoteStatus')).toContainText(['Latest quote not reverified','Latest quote not reverified']);
 await page.evaluate(()=>{(window as any).launchHidden=false;document.dispatchEvent(new Event('visibilitychange'))});await expect(panel(page)).toContainText(`Block ${head+1}`);await expect(panel(page).locator('.marketQuoteStatus')).toContainText(['Fresh oracle round','Fresh oracle round']);
});
test('market: authentication failure exposes no market network calls or private context',async({page})=>{
 await account(page,false);const state=await rpc(page);await page.goto('/workspace/overview',{waitUntil:'domcontentloaded'});await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();expect(state.batches).toBe(0);await expect(panel(page)).toHaveCount(0);
});
test('market: GasGuard uses same genuine observations without automatically simulating transactions',async({page})=>{
 let simulations=0,snapshots=0;await page.route('**/api/v1/defi/transaction**',route=>{simulations++;return route.fulfill({status:400,json:{error:{message:'Not requested'}}})});
 await page.route('**/api/v1/defi/snapshot',route=>{snapshots++;return route.fulfill({status:400,json:{error:{message:'Not requested'}}})});
 await open(page,'success','/workspace/transactions');
 await expect(panel(page)).toContainText(`Block ${head}`);await expect(panel(page).getByRole('img',{name:'Ethereum observed base fee history'})).toBeVisible();await expect(panel(page)).toContainText('independent call-specific estimates');expect(simulations).toBe(0);expect(snapshots).toBe(0);
});
test('market: mobile quote charts and refresh remain usable without horizontal overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});await open(page);await expect(panel(page)).toContainText('Fresh block observation');await expect(panel(page).getByRole('button',{name:'Refresh market context',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);
});

for(const width of [1440,390])test(`market clarity: separated metrics, sticky context and readable chart controls at ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900});await open(page);await expect(panel(page)).toContainText('Fresh block observation');await page.evaluate(()=>document.fonts.ready);
 const metrics=page.getByRole('region',{name:'Current analysis overview'});await expect(metrics.locator('article')).toHaveCount(3);await expect(metrics).toContainText('Inspect a wallet to view this metric');
 const grid=await metrics.evaluate(el=>getComputedStyle(el).display);expect(grid).toBe('grid');
 const chart=panel(page).locator('figure').filter({hasText:'ETH / USD · observed oracle history'});const before=await chart.locator('.chartReadout').innerText();await chart.getByRole('img').focus();await page.keyboard.press('ArrowLeft');await expect(chart.locator('.chartReadout')).not.toHaveText(before);
 await page.evaluate(()=>window.scrollTo(0,400));const header=await page.locator('.workspaceHeaderBar').boundingBox(),scope=await page.locator('.workspaceScope').boundingBox();expect(scope!.y).toBeGreaterThanOrEqual(header!.y+header!.height-1);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:`../../../../outputs/workspace-clarity-fixture-${width}.png`,fullPage:true});
});
