import {snapshot,gasguard,COVERAGE} from './defi-portfolio-rpc.mjs';
import {client} from './defi-rpc.mjs';

// The database gate is atomic across all isolates. There is no in-memory quota fallback.
export async function handleDefi(req,path,admin,rpcUrl) {
  const respond=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'}});
  if(req.method!=='POST')return respond({detail:'POST required'},405);
  if(Number(req.headers.get('content-length')||0)>4096)return respond({detail:'Request is too large'},413);
  const raw=await req.text();if(raw.length>4096)return respond({detail:'Request is too large'},413);
  let input;try{input=JSON.parse(raw);}catch{return respond({detail:'Invalid JSON'},422);}
  if(!input||typeof input.wallet!=='string'||!/^0x[0-9a-fA-F]{40}$/.test(input.wallet))return respond({detail:'Enter a valid Ethereum wallet address'},422);
  if(input.coverage!==undefined&&!COVERAGE.includes(input.coverage))return respond({detail:'Unsupported coverage'},422);
  if(!['/api/v1/defi/snapshot','/api/v1/defi/transaction'].includes(path))return respond({detail:'Unsupported endpoint'},404);
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
