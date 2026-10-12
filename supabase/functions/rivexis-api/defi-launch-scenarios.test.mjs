// Deliberately synthetic contract responses: validation evidence, not live holdings.
import test from 'node:test';
import assert from 'node:assert/strict';
import {sampleSnapshot} from './defi-sample.mjs';
import {scenario,frontier,metrics,WAD} from './defi-model.mjs';
import {gasguard as aaveGasguard,snapshot,POOL,ORACLE} from './defi-rpc.mjs';
import {gasguard as portfolioGasguard} from './defi-portfolio-rpc.mjs';

const now=1791550000000, state=()=>sampleSnapshot(now);
const asset='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',wallet='0x'+'1'.repeat(40);
function reference(position,shock={}) {
  let collateral=0n,debt=0n,weighted=0n;
  for(const r of position.reserves){
    const price=BigInt(r.priceRaw)*BigInt(10000+(shock[r.asset.toLowerCase()]??0))/10000n,unit=10n**BigInt(r.decimals);
    const c=BigInt(r.collateralRaw)*price/unit;
    debt+=(BigInt(r.debtRaw)*price+unit-1n)/unit;
    if(r.collateralEnabled){collateral+=c;weighted+=c*BigInt(r.ltBps)}
  }
  return {collateralRaw:String(collateral),debtRaw:String(debt),healthFactorRaw:debt?String((weighted*WAD+debt/2n)/debt/10000n):null};
}
function checkReference(s,shock={}){const actual=scenario(s,shock,[],now)[0];const expected=reference(s.positions[0],shock);for(const key of Object.keys(expected))assert.equal(actual[key],expected[key]);return actual}
test('LG01 independent baseline accounting',()=>checkReference(state()));
test('LG02 collateral crash -50% crosses threshold',()=>{const s=state();assert.equal(checkReference(s,{[s.positions[0].reserves[0].asset.toLowerCase()]:-5000}).liquidatable,true)});
test('LG03 debt depeg +25% uses debt oracle, independently',()=>{const s=state();checkReference(s,{[s.positions[0].reserves[1].asset.toLowerCase()]:2500})});
test('LG04 simultaneous correlated collateral/debt moves',()=>{const s=state();checkReference(s,{[s.positions[0].reserves[0].asset.toLowerCase()]:-2000,[s.positions[0].reserves[1].asset.toLowerCase()]:1000})});
test('LG05 zero debt is unbounded health, never zero',()=>{const s=state();s.positions[0].reserves[1].debtRaw='0';assert.equal(checkReference(s).healthFactorRaw,null)});
test('LG06 exact liquidation boundary HF 1 is not below threshold',()=>{const s=state();s.positions[0].reserves[1].debtRaw='24000000000';assert.equal(checkReference(s).healthFactorRaw,String(WAD));assert.equal(checkReference(s).liquidatable,false)});
test('LG07 one-unit debt dust uses ceiling',()=>{const s=state();s.positions[0].reserves[1].debtRaw='1';s.positions[0].reserves[1].priceRaw='100000001';assert.equal(checkReference(s).debtRaw,'101')});
test('LG08 unsupported or malformed scenario input fails closed',()=>{const s=state();for(const shocks of [{[asset]:-9501},{[asset]:NaN},{['0x'+'2'.repeat(40)]:100},[]])assert.throws(()=>scenario(s,shocks,[],now))});
test('LG09 stale and future snapshot evidence cannot calculate',()=>{for(const offset of [-181,31]){const s=state();s.blockTimestamp+=offset;assert.throws(()=>scenario(s,{},[],now),/stale/)}});
test('LG10 repeated operations are deterministic and do not mutate inputs',()=>{const s=state(),before=JSON.stringify(s);for(let i=0;i<20;i++)assert.deepEqual(checkReference(s),checkReference(s));assert.equal(JSON.stringify(s),before)});
test('LG11 mixed collateral thresholds retain fractional weighted numerator',()=>{const s=state(),r=s.positions[0].reserves[1];r.collateralEnabled=true;r.collateralRaw='100000001';r.ltBps='7351';checkReference(s)});

function rpcFixture(options={}){
  const block={number:100n,hash:'0x'+'a'.repeat(64),timestamp:BigInt(Math.floor(Date.now()/1000))};let changed=false;
  const result=c=>{
    switch(c.functionName){
      case 'getPoolDataProvider':return '0x'+'2'.repeat(40);case 'getPool':return POOL;case 'getPriceOracle':return ORACLE;
      case 'BASE_CURRENCY_UNIT':return 100000000n;case 'getReservesList':return [asset];case 'getUserEMode':return 0n;
      case 'getUserAccountData':return [300000000000n,150000000000n,0n,8000n,7500n,1600000000000000000n];
      case 'getUserReserveData':return [10n**18n,0n,5n*10n**17n,0n,5n*10n**17n,0n,0n,block.timestamp,true];
      case 'getConfiguration':return 7500n|(8000n<<16n)|(18n<<48n)|(1n<<56n)|(1n<<58n);
      case 'getAssetPrice':return 300000000000n;case 'getSourceOfAsset':return '0x5424384b256154046e9667ddfaaa5e550145215e';
      case 'symbol':return 'WETH';case 'balanceOf':return options.balance??10n**18n;case 'allowance':return options.allowance??10n**18n;
      case 'latestRoundData':return [1n,300000000000n,block.timestamp,options.oracleStale?block.timestamp-4201n:block.timestamp,1n];
      default:throw Error('Unexpected fixture contract read');
    }
  };
  return {transport:{url:'https://fixture.invalid'},getChainId:async()=>options.chain??1,
    getBlock:async({blockNumber})=>{if(blockNumber)assert.equal(blockNumber,100n);return {...block,timestamp:options.stale?block.timestamp-181n:block.timestamp,hash:changed?'0x'+'b'.repeat(64):block.hash}},
    getStorageAt:async({blockNumber})=>{assert.equal(blockNumber,100n);return '0x'+'0'.repeat(24)+'728a138a4823392c2efa55e028d434f526fe03cf'},
    multicall:async({blockNumber,contracts})=>{assert.equal(blockNumber,100n);return contracts.map(c=>({status:'success',result:result(c)}))},
    getBalance:async({blockNumber})=>{assert.equal(blockNumber,100n);return options.native??10n**18n},
    call:async(args)=>{assert.equal(args.blockNumber,100n);assert.equal(args.account.toLowerCase(),wallet);if(options.callFailure)throw Error('provider call unavailable');return {data:'0x'}},
    estimateGas:async({blockNumber})=>{assert.equal(blockNumber,100n);if(options.gasFailure)throw Error('gas RPC unavailable');return Object.hasOwn(options,'gas')?options.gas:100000n},
    estimateFeesPerGas:async()=>options.fees??{maxFeePerGas:1000000000n},
    getTransactionCount:async({blockNumber})=>{assert.equal(blockNumber,100n);if(options.reorg)changed=true;return 7},
  };
}
test('LG12 provider outage cannot return a fabricated supported snapshot',async()=>{const rpc=rpcFixture();rpc.getChainId=async()=>{throw Error('RPC unavailable')};await assert.rejects(snapshot(wallet,rpc),/RPC unavailable/)});
test('LG13 stale oracle remains unsupported even when Ethereum block is fresh',async()=>{const s=await snapshot(wallet,rpcFixture({oracleStale:true}));assert.equal(s.status,'UNSUPPORTED');assert.equal(s.positions[0].reserves[0].oracleState,'UNVALIDATED');assert.throws(()=>scenario(s))});
for(const [name,preview] of [['Aave',aaveGasguard],['portfolio',portfolioGasguard]]){
  const run=(input={},options={})=>preview({wallet,asset,kind:'withdraw',amount:'0.1',...input},rpcFixture(options));
  test(`GG01 ${name} successful withdrawal has independently calculated health and fees`,async()=>{const r=await run();assert.equal(r.after.healthFactorRaw,'1440000000000000000');assert.equal(r.feeReserveWei,'120000000000000');assert.equal(r.nonceAtBlock,7);assert.equal(r.status,'PREVIEW_ONLY')});
  test(`GG02 ${name} successful repay lowers debt exactly`,async()=>{const r=await run({kind:'repay'});assert.equal(r.after.healthFactorRaw,'2000000000000000000');assert.equal(r.after.debtRaw,'120000000000')});
  test(`GG03 ${name} successful supply raises adjusted collateral exactly`,async()=>{const r=await run({kind:'supply'});assert.equal(r.after.healthFactorRaw,'1760000000000000000')});
  test(`GG04 ${name} borrow raises debt without crediting collateral`,async()=>{const r=await run({kind:'borrow'});assert.equal(r.after.healthFactorRaw,'1333333333333333333')});
  test(`GG05 ${name} missing token allowance produces explicit blocker`,async()=>{const r=await run({kind:'repay'},{allowance:0n});assert.equal(r.status,'BLOCKED');assert.match(r.blockers.join(' '),/allowance/) });
  test(`GG06 ${name} insufficient wallet and native balances are separately blocked`,async()=>{const r=await run({kind:'repay'},{balance:0n,native:0n});assert.match(r.blockers.join(' '),/wallet token balance/);assert.match(r.blockers.join(' '),/native ETH/) });
  test(`GG07 ${name} excess withdrawal/repayment and zero/unsafe amounts reject`,async()=>{for(const input of [{amount:'1.01'},{kind:'repay',amount:'0.51'},{amount:'0'},{amount:'NaN'},{amount:'1e3'}])await assert.rejects(run(input))});
  test(`GG08 ${name} unsupported asset and action reject`,async()=>{for(const input of [{asset:'0x'+'3'.repeat(40)},{kind:'swap'}])await assert.rejects(run(input))});
  test(`GG09 ${name} RPC call and gas estimation failures remain unverified`,async()=>{for(const o of [{callFailure:true},{gasFailure:true}]){const r=await run({},o);assert.equal(r.status,'BLOCKED');assert.equal(r.simulation,'REVERTED_OR_RPC_UNAVAILABLE')}});
  test(`GG10 ${name} wrong chain, stale block and preview reorg reject`,async()=>{for(const o of [{chain:137},{stale:true},{reorg:true}])await assert.rejects(run({},o))});
  test(`GG11 ${name} repeated previews preserve raw amounts and do not mutate input`,async()=>{const input={amount:'0.1'},before=JSON.stringify(input);const a=await run(input),b=await run(input);assert.deepEqual(a,b);assert.equal(JSON.stringify(input),before)});
  test(`GG12 ${name} liquidation-crossing withdrawal is blocked`,async()=>{const r=await run({amount:'0.5'});assert.equal(r.after.healthFactorRaw,'800000000000000000');assert.equal(r.status,'BLOCKED');assert.match(r.blockers.join(' '),/liquidation threshold/)});
  test(`GG13 ${name} missing, zero, negative and malformed fee evidence blocks affordability`,async()=>{for(const fees of [{},{maxFeePerGas:0n},{maxFeePerGas:-1n},{maxFeePerGas:'1000000000'}]){const r=await run({},{fees});assert.equal(r.status,'BLOCKED');assert.equal(r.feeReserveWei,null);assert.equal(r.maxFeePerGasRaw,null);assert.match(r.blockers.join(' '),/fee evidence is unavailable/)}});
  test(`GG14 ${name} missing or malformed gas estimate cannot invent execution costs`,async()=>{for(const gas of [null,0n,-1n,'100000']){const r=await run({},{gas});assert.equal(r.status,'BLOCKED');assert.equal(r.gasRaw,null);assert.equal(r.feeReserveWei,null);assert.match(r.blockers.join(' '),/valid gas estimate is unavailable/)}});
  test(`GG15 ${name} legacy gas price remains valid independently checked evidence`,async()=>{const r=await run({},{fees:{gasPrice:2000000000n}});assert.equal(r.status,'PREVIEW_ONLY');assert.equal(r.feeReserveWei,'240000000000000')});
}

const plan=(s=state(),c={})=>frontier(s,{budget:'3000',target:'1.5',gasReserve:'25',...c},now);
test('DP01 repayment target is feasible within constrained capital',()=>{const r=plan();assert.equal(r.meetsTarget,true);for(const a of r.alternatives)assert.ok(BigInt(a.totalBudgetRaw)<=300000000000n)});
test('DP02 zero-cost baseline wins already-satisfied objective',()=>{const r=plan(state(),{target:'1.2'});assert.deepEqual(r.alternatives[0].actions,[]);assert.equal(r.alternatives[0].totalBudgetRaw,'0')});
test('DP03 zero budget exposes no unsupported target solution',()=>{assert.equal(plan(state(),{budget:'0',gasReserve:'0',target:'2'}).alternatives.length,0)});
test('DP04 fee reserve exceeding budget is rejected',()=>assert.throws(()=>plan(state(),{budget:'10',gasReserve:'11'})));
test('DP05 insufficient native ETH withholds transaction candidates',()=>{const s=state();s.nativeBalanceRaw='0';assert.equal(plan(s).alternatives.length,0)});
test('DP06 absent token balance cannot create capital',()=>{const s=state();s.positions[0].reserves.forEach(r=>r.walletRaw='0');assert.equal(plan(s).alternatives.length,0)});
test('DP07 malformed target, budget and objective reject',()=>{for(const c of [{target:'0.99'},{target:'10.01'},{budget:'-1'},{budget:'Infinity'},{objective:'guaranteed-safe'}])assert.throws(()=>plan(state(),c))});
test('DP08 severe market stress can leave target unachievable honestly',()=>{const s=state();assert.equal(plan(s,{budget:'100',gasReserve:'0',shocks:{[asset]:-9000}}).meetsTarget,false)});
test('DP09 two positions share actual wallet balances without netting',()=>{const s=state(),second=structuredClone(s.positions[0]);second.id='independent-second';second.reserves[0].collateralRaw='8000000000000000000';s.positions.push(second);const r=plan(s,{budget:'5000',gasReserve:'0',target:'1.3',objective:'max-min'});assert.equal(r.baseline.length,2);assert.ok(r.alternatives.some(a=>new Set(a.actions.map(x=>x.positionId)).size===2));for(const a of r.alternatives)for(const reserve of s.positions[0].reserves)assert.ok(a.actions.filter(x=>x.asset===reserve.asset).reduce((n,x)=>n+BigInt(x.amountRaw),0n)<=BigInt(reserve.walletRaw))});
test('DP10 repeated comparisons are deterministic with unchanged evidence',()=>{const s=state(),before=JSON.stringify(s),a=plan(s);for(let i=0;i<10;i++)assert.deepEqual(plan(s),a);assert.equal(JSON.stringify(s),before)});
test('DP11 stale or unvalidated oracle evidence cannot produce alternatives',()=>{const s=state();s.blockTimestamp-=181;assert.throws(()=>plan(s));const t=state();t.positions[0].reserves[0].oracleState='UNVALIDATED';assert.throws(()=>plan(t))});
test('DP12 every alternative outcome reconciles independently after exact actions',()=>{const s=state();for(const a of plan(s).alternatives){const copy=structuredClone(s);for(const action of a.actions){const r=copy.positions.find(p=>p.id===action.positionId).reserves.find(r=>r.asset===action.asset);const key=action.kind==='repay'?'debtRaw':'collateralRaw';r[key]=String(BigInt(r[key])+(action.kind==='repay'?-1n:1n)*BigInt(action.amountRaw))}for(let i=0;i<copy.positions.length;i++){const expected=reference(copy.positions[i]);for(const key of Object.keys(expected))assert.equal(a.outcomes[i][key],expected[key])}}});
