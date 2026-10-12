import {getAddress,keccak256,parseAbi} from 'viem';
import {client} from './defi-rpc.mjs';
import {validWallet,readRequestText} from './defi-http.mjs';
const metadataAbi=parseAbi(['function name() view returns (string)','function symbol() view returns (string)','function decimals() view returns (uint8)','function totalSupply() view returns (uint256)']);
const slots={implementation:'0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc',beacon:'0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50'};
const stringify=value=>JSON.parse(JSON.stringify(value,(_,v)=>typeof v==='bigint'?v.toString():v));
const storageAddress=value=>typeof value!=='string'||!/^0x0{24}[0-9a-f]{40}$/i.test(value)?'UNKNOWN':/^0x0{64}$/i.test(value)?null:getAddress('0x'+value.slice(-40));
export async function handleOnChain(req,path,admin,rpcUrl,rpcFactory=client){
 const respond=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'}});
 if(req.method!=='POST')return respond({detail:'POST required'},405);
 if(!['/api/v1/on-chain/contract','/api/v1/on-chain/read','/api/v1/on-chain/network','/api/v1/on-chain/wallet'].includes(path))return respond({detail:'Unsupported on-chain endpoint'},404);
 let input;try{input=JSON.parse(await readRequestText(req,8192))}catch{return respond({detail:'Invalid or oversized inspection request'},422)}
 const network=path.endsWith('/network'),read=path.endsWith('/read');
 if(!input||Array.isArray(input)||typeof input!=='object'||input.chainId!==1||Object.keys(input).some(k=>!['chainId','address',...(read?['data']:[])].includes(k)))return respond({detail:'Ethereum mainnet and supported inspection fields are required'},422);
 if(!network&&!validWallet(input.address))return respond({detail:'Enter a valid Ethereum address; mixed-case addresses require a correct checksum'},422);
 if(read&&(typeof input.data!=='string'||!/^0x[0-9a-f]{8}(?:[0-9a-f]{2})*$/i.test(input.data)||input.data.length>4098))return respond({detail:'Read calldata must be bounded hexadecimal data with a function selector'},422);
 const address=network?'0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2':getAddress(input.address);
 let quota;try{quota=await admin.rpc('rivexis_defi_quota',{p_wallet:address.toLowerCase()})}catch{return respond({detail:'Quota service unavailable; no RPC request was made'},503)}
 if(quota.error)return respond({detail:'Quota service unavailable; no RPC request was made'},503);
 if(quota.data!==true)return respond({detail:'Beta inspection quota reached. Try later.'},429);
 try{
  const rpc=rpcFactory(rpcUrl);if(await rpc.getChainId()!==1)throw Error('Network identity mismatch');
  const block=await rpc.getBlock();if(!block.hash||block.number==null||Math.abs(Date.now()/1000-Number(block.timestamp))>180)throw Error('Stale or incomplete block evidence');
  const blockNumber=block.number,evidence={chainId:1,network:'Ethereum mainnet',blockNumber:String(blockNumber),blockHash:block.hash,blockTimestamp:Number(block.timestamp),observedAt:new Date().toISOString()};
  let result;
  if(network)result={status:'OBSERVED',...evidence};
  else if(path.endsWith('/wallet'))result={status:'OBSERVED',...evidence,address,balanceWei:String(await rpc.getBalance({address,blockNumber}))};
  else{
   const code=await rpc.getCode({address,blockNumber});
   if(!code||code==='0x')result={status:'NO_CONTRACT_CODE',...evidence,address,codeDetected:false,sourceVerified:false};
   else if(read){const response=await rpc.call({to:address,data:input.data,gas:500000n,blockNumber});if(!response.data||response.data.length>32770)throw Error('Unavailable or oversized call output');result={status:'OBSERVED',...evidence,address,data:response.data,execution:'eth_call only; no state persisted',sourceVerified:false};}
   else{
    const metadata=await Promise.all(metadataAbi.map(async fn=>{try{const value=await rpc.readContract({address,abi:metadataAbi,functionName:fn.name,blockNumber,gas:500000n});if(typeof value==='string'&&value.length>128)return [fn.name,{status:'UNKNOWN'}];return [fn.name,{status:'OBSERVED',value:stringify(value)}]}catch{return [fn.name,{status:'UNKNOWN'}]}}));
    const proxy={};for(const [kind,slot] of Object.entries(slots)){try{proxy[kind]=storageAddress(await rpc.getStorageAt({address,slot,blockNumber}))}catch{proxy[kind]='UNKNOWN'}}
    let implementationCodeHash=null;if(proxy.implementation&&proxy.implementation!=='UNKNOWN'){const implementationCode=await rpc.getCode({address:proxy.implementation,blockNumber});implementationCodeHash=implementationCode&&implementationCode!=='0x'?keccak256(implementationCode):null;}
    result={status:'OBSERVED',...evidence,address,codeDetected:true,codeBytes:(code.length-2)/2,codeHash:keccak256(code),metadata:Object.fromEntries(metadata),proxy:{...proxy,implementationCodeHash,scope:'EIP-1967 implementation and beacon slots only; other proxy patterns are not ruled out'},sourceVerified:false,abiVerified:false,classification:'Deployed bytecode; metadata responses do not establish full ERC-20 compliance or safety'};
   }
  }
  const final=await rpc.getBlock({blockNumber});if(final.hash!==block.hash||await rpc.getChainId()!==1)throw Error('Block or network changed during inspection');
  return respond(result);
 }catch{return respond({status:'UNKNOWN',detail:'On-chain evidence unavailable, stale, reverted or inconsistent. No contract safety or financial result has been inferred.'},503)}
}
