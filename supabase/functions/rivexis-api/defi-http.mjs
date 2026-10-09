import {snapshot,gasguard,COVERAGE} from './defi-portfolio-rpc.mjs';
import {client} from './defi-rpc.mjs';
import {isAddress} from 'viem';
import {decimal,integer} from './defi-model.mjs';

export function validWallet(wallet){
  return typeof wallet==='string'&&isAddress(wallet,{strict:true})&&!/^0x0{40}$/i.test(wallet);
}
// Count bytes while streaming; Content-Length may be missing or inaccurate.
// Cancelling the reader prevents oversized bodies from being fully buffered.
export async function readRequestText(req,limit=4096){
  if(Number(req.headers.get('content-length')||0)>limit)throw new Error('Request is too large');
  if(!req.body)return '';
  const reader=req.body.getReader(),chunks=[];let size=0;
  try{
    while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;
      if(size>limit){await reader.cancel();throw new Error('Request is too large');}chunks.push(value);}
  }finally{reader.releaseLock();}
  const bytes=new Uint8Array(size);let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  return new TextDecoder('utf-8',{fatal:true}).decode(bytes);
}
function transactionInputError(input){
  if(!['repay','supply','withdraw','borrow'].includes(input.kind))return 'Unsupported transaction';
  if(!validWallet(input.asset))return 'Enter a valid token address';
  try{if(decimal(input.amount,18)===0n)return 'Amount must be greater than zero';}
  catch{return 'Enter a positive decimal token amount with at most 18 decimal places';}
  if(input.positionId!==undefined&&(typeof input.positionId!=='string'||!/^((aave-v3:1)|(morpho-blue:1:0x[0-9a-fA-F]{64})):0x[0-9a-fA-F]{40}$/.test(input.positionId)))return 'Invalid transaction position';
  if(input.sharesRaw!==undefined){
    try{if(input.kind!=='repay'||integer(input.sharesRaw)===0n)return 'Invalid repayment shares';}
    catch{return 'Invalid repayment shares';}
  }
  return null;
}

// The database gate is atomic across all isolates. There is no in-memory quota fallback.
export async function handleDefi(req,path,admin,rpcUrl) {
  const respond=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'}});
  if(req.method!=='POST')return respond({detail:'POST required'},405);
  let raw;try{raw=await readRequestText(req);}catch(cause){return respond({detail:cause?.message==='Request is too large'?'Request is too large':'Invalid request body'},cause?.message==='Request is too large'?413:422);}
  let input;try{input=JSON.parse(raw);}catch{return respond({detail:'Invalid JSON'},422);}
  if(!input||typeof input!=='object'||Array.isArray(input)||!validWallet(input.wallet))return respond({detail:'Enter a valid Ethereum wallet address'},422);
  if(input.coverage!==undefined&&!COVERAGE.includes(input.coverage))return respond({detail:'Unsupported coverage'},422);
  if(!['/api/v1/defi/snapshot','/api/v1/defi/transaction'].includes(path))return respond({detail:'Unsupported endpoint'},404);
  if(path.endsWith('/transaction')){const detail=transactionInputError(input);if(detail)return respond({detail},422);}
  const {data,error}=await admin.rpc('rivexis_defi_quota',{p_wallet:input.wallet.toLowerCase()});
  if(error)return respond({detail:'Analysis quota service is unavailable; no RPC request was made'},503);
  if(data!==true)return respond({detail:'Free beta quota reached. Limit: 300 requests per day globally and 4 per wallet per minute. Try later.'},429);
  try {return respond(path.endsWith('/snapshot')?await snapshot(input.wallet,client(rpcUrl),input.coverage??'aave'):await gasguard(input,client(rpcUrl)));}
  catch(cause){
    const reason=cause?.shortMessage??cause?.message??'Protocol evidence unavailable';
    const validation=/valid|Unsupported|Amount|decimal|exceeds|stale|Snapshot|Reserve|Insufficient|greater than/.test(reason);
    return respond({status:'UNKNOWN',detail:validation?reason.slice(0,240):'Ethereum RPC or protocol evidence is unavailable. No financial result has been inferred.'},validation?422:503);
  }
}
