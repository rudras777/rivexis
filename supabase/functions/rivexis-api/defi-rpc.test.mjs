import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {getAddress,isAddress} from 'viem';
import {snapshot,gasguard,POOL,ORACLE} from './defi-rpc.mjs';
import {gasguard as portfolioGasguard} from './defi-portfolio-rpc.mjs';

const wallet='0x'+'1'.repeat(40),asset='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2';
// A synthetic WETH-only account; no live provider or claimed production holdings.
function rpcFixture({reorgOnNonce=false,reorgOnBalance=false}={}){
  const block={number:100n,hash:'0x'+'a'.repeat(64),timestamp:BigInt(Math.floor(Date.now()/1000))};
  let changed=false;const reads=[];
  const result=contract=>{
    switch(contract.functionName){
      case 'getPoolDataProvider':return '0x'+'2'.repeat(40);
      case 'getPool':return POOL;
      case 'getPriceOracle':return ORACLE;
      case 'BASE_CURRENCY_UNIT':return 100000000n;
      case 'getReservesList':return [asset];
      case 'getUserEMode':return 0n;
      case 'getUserAccountData':return [300000000000n,150000000000n,0n,8000n,7500n,1600000000000000000n];
      case 'getUserReserveData':return [10n**18n,0n,5n*10n**17n,0n,5n*10n**17n,0n,0n,block.timestamp,true];
      case 'getConfiguration':return 7500n|(8000n<<16n)|(18n<<48n)|(1n<<56n)|(1n<<58n);
      case 'getAssetPrice':return 300000000000n;
      case 'getSourceOfAsset':return '0x5424384b256154046e9667ddfaaa5e550145215e';
      case 'symbol':return 'WETH';
      case 'balanceOf':case 'allowance':return 10n**18n;
      case 'latestRoundData':return [1n,300000000000n,block.timestamp,block.timestamp,1n];
      default:throw new Error('Unexpected fixture contract read');
    }
  };
  const rpc={
    transport:{url:'https://fixture.invalid'},
    getChainId:async()=>1,
    getBlock:async({blockNumber})=>{reads.push('block');if(blockNumber)assert.equal(blockNumber,block.number);return {...block,hash:changed?'0x'+'b'.repeat(64):block.hash};},
    getStorageAt:async({blockNumber})=>{assert.equal(blockNumber,block.number);return '0x'+'0'.repeat(24)+'728a138a4823392c2efa55e028d434f526fe03cf';},
    multicall:async({blockNumber,contracts})=>{assert.equal(blockNumber,block.number);return contracts.map(c=>({status:'success',result:result(c)}));},
    getBalance:async({blockNumber})=>{assert.equal(blockNumber,block.number);reads.push('balance');if(reorgOnBalance)changed=true;return 10n**18n;},
    call:async({blockNumber})=>{assert.equal(blockNumber,block.number);return {data:'0x'};},
    estimateGas:async({blockNumber})=>{assert.equal(blockNumber,block.number);return 100000n;},
    estimateFeesPerGas:async()=>({maxFeePerGas:1000000000n}),
    getTransactionCount:async({blockNumber})=>{assert.equal(blockNumber,block.number);reads.push('nonce');if(reorgOnNonce)changed=true;return 7;},
  };
  return {rpc,reads};
}
test('pinned Aave snapshot rejects a reorganization during the balance read',async()=>{
  await assert.rejects(snapshot(wallet,rpcFixture({reorgOnBalance:true}).rpc),/Block changed/);
});
test('Morpho-only portfolio rejects a reorganization during the final native balance read',async()=>{
  // Isolate contract discovery for an empty market; exercise the real orchestration.
  const source=readFileSync(new URL('./defi-portfolio-rpc.mjs',import.meta.url),'utf8').replace(/^import .*;\r?$/gm,'').replace(/^export /gm,'');
  const context=vm.createContext({getAddress,isAddress,Date,MODEL:'ethereum-lending-1',readMorphoPosition:async()=>null});
  new vm.Script(source+'\nthis.snapshotUnderTest=snapshot;').runInContext(context);
  await assert.rejects(context.snapshotUnderTest(wallet,rpcFixture({reorgOnBalance:true}).rpc,'morpho-wbtc'),/Block changed/);
});
for(const [name,preview] of [['Aave',gasguard],['portfolio',portfolioGasguard]]){
  test(`${name} transaction rejects a reorganization during the nonce read`,async()=>{
    await assert.rejects(preview({wallet,asset,kind:'withdraw',amount:'0.001'},rpcFixture({reorgOnNonce:true}).rpc),/Block changed/);
  });
  test(`${name} stable-block preview retains the observed nonce and modeled health`,async()=>{
    const {rpc}=rpcFixture();const result=await preview({wallet,asset,kind:'withdraw',amount:'0.001'},rpc);
    assert.equal(result.simulation,'SUCCEEDED_AT_BLOCK');assert.equal(result.nonceAtBlock,7);
    assert.equal(result.before.healthFactorRaw,'1600000000000000000');assert.equal(result.after.healthFactorRaw,'1598400000000000000');
  });
}
