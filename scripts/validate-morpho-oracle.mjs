// Same-block, read-only staging gate. Not a production discovery endpoint.
import {mkdir,writeFile} from 'node:fs/promises';
import {parseAbi,keccak256,encodeAbiParameters} from 'viem';
import {client} from '../supabase/functions/rivexis-api/defi-rpc.mjs';
import {MORPHO_WBTC as config,validateMorphoWbtcOracle} from '../supabase/functions/rivexis-api/defi-morpho-oracle.mjs';
const core='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';
const abi=parseAbi(['function idToMarketParams(bytes32) view returns(address,address,address,address,uint256)',
  'function VAULT() view returns(address)','function VAULT_CONVERSION_SAMPLE() view returns(uint256)',
  'function BASE_FEED_1() view returns(address)','function BASE_FEED_2() view returns(address)',
  'function QUOTE_FEED_1() view returns(address)','function QUOTE_FEED_2() view returns(address)',
  'function SCALE_FACTOR() view returns(uint256)','function price() view returns(uint256)',
  'function decimals() view returns(uint8)','function latestRoundData() view returns(uint80,int256,uint256,uint256,uint80)']);
const rpc=client(),block=await rpc.getBlock({blockTag:'latest'}),blockNumber=block.number;
if(await rpc.getChainId()!==1)throw new Error('Not Ethereum');
const read=(address,functionName,args=[])=>({address,abi,functionName,args});
const names=['VAULT','VAULT_CONVERSION_SAMPLE','BASE_FEED_1','BASE_FEED_2','QUOTE_FEED_1','QUOTE_FEED_2','SCALE_FACTOR','price'];
const [params,...values]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(core,'idToMarketParams',[config.marketId]),...names.map(n=>read(config.oracle,n))]});
const marketId=keccak256(encodeAbiParameters([{type:'address'},{type:'address'},{type:'address'},{type:'address'},{type:'uint256'}],params));
const readings=await rpc.multicall({allowFailure:false,blockNumber,contracts:[...values.slice(2,5).flatMap(a=>[read(a,'decimals'),read(a,'latestRoundData')]),read(params[0],'decimals'),read(params[1],'decimals')]});
const evidence={marketId,loanToken:params[0],collateralToken:params[1],oracle:params[2],irm:params[3],lltvRaw:params[4].toString(),
  codeHash:keccak256(await rpc.getCode({address:config.oracle,blockNumber})),vault:values[0],vaultConversionSample:values[1],quoteFeed2:values[5],scaleFactor:values[6],price:values[7],
  loanDecimals:readings[6],collateralDecimals:readings[7],blockTimestamp:block.timestamp,
  feeds:config.feeds.map((f,i)=>({kind:f.kind,address:values[i+2],decimals:readings[i*2],round:readings[i*2+1],maxAgeSeconds:f.maxAge}))};
if(!validateMorphoWbtcOracle(evidence))throw new Error('Morpho pinned oracle validation failed');
if((await rpc.getBlock({blockNumber})).hash!==block.hash)throw new Error('Reference block reorganized');
const report={classification:'STAGING_ORACLE_VALIDATION_NOT_PRODUCTION_SUPPORT',status:'PINNED_ORACLE_REFERENCE_PASS',checkedAt:new Date().toISOString(),blockNumber:blockNumber.toString(),blockHash:block.hash,
  source:'https://github.com/morpho-org/morpho-blue-oracles/blob/6941f06e411ca17c692fc63824cc60eeeec0035e/src/ChainlinkOracle.sol',evidence,
  limitations:['One Ethereum WBTC/USDC 86% LLTV market only; other markets are unvalidated.','Feed freshness bounds are beta assumptions, not protocol guarantees.','Contract and oracle validation does not certify RPC independence, liquidity or execution.','Production discovery, shared-budget planning and transaction support remain disabled.']};
await mkdir('certification-reports',{recursive:true});
await writeFile('certification-reports/morpho-oracle-reference.json',JSON.stringify(report,(_,v)=>typeof v==='bigint'?v.toString():v,2));
console.log(JSON.stringify({status:report.status,blockNumber:report.blockNumber,marketId,priceRaw:evidence.price.toString(),productionSupport:false},null,2));
