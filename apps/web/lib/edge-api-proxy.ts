const EDGE_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-api";
const DECISION_REPORT_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-decision-reports";
const ALERTS_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-alerts";
const WRITE_METHODS=new Set(["POST","PUT","PATCH","DELETE"]);
const MAX_REQUEST_BYTES=128*1024;

function rejection(status:number,detail:string){
  return Response.json({detail},{status,headers:{"cache-control":"no-store"}});
}

// Login/recovery intentionally have no session CSRF token yet. CORS alone does
// not stop a cross-site request from being processed or setting a login cookie.
function writeOriginAllowed(request:Request){
  const origin=request.headers.get("origin");
  if(request.headers.get("sec-fetch-site")==="cross-site")return false;
  if(origin===null)return true; // Non-browser clients still face upstream auth/CSRF.
  return origin===new URL(request.url).origin;
}

async function boundedBody(request:Request):Promise<Uint8Array<ArrayBuffer>|Response|undefined>{
  const declared=request.headers.get("content-length");
  if(declared!==null&&(!/^\d+$/.test(declared)||Number(declared)>MAX_REQUEST_BYTES))return rejection(413,"Request body exceeds the supported size");
  if(!request.body)return undefined;
  const reader=request.body.getReader(),chunks:Uint8Array[]=[];
  let bytes=0;
  try{
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      bytes+=value.byteLength;
      if(bytes>MAX_REQUEST_BYTES){void reader.cancel().catch(()=>{});return rejection(413,"Request body exceeds the supported size")}
      chunks.push(value);
    }
  }catch{return rejection(400,"Request body could not be read")}
  finally{reader.releaseLock()}
  const body=new Uint8Array(bytes);let offset=0;
  for(const chunk of chunks){body.set(chunk,offset);offset+=chunk.byteLength}
  return body;
}

const SAMPLE_EVM_ADDRESSES=new Set([
  "0x1111111111111111111111111111111111111111",
  "0x2222222222222222222222222222222222222222",
]);

function upstreamBase(path:string){
  if(path==="/api/v1/history"||path.startsWith("/api/v1/decisions/")||path==="/api/v1/reports"||path.startsWith("/api/v1/reports/"))return DECISION_REPORT_API_URL;
  if(path==="/api/v1/alerts"||path.startsWith("/api/v1/alerts/"))return ALERTS_API_URL;
  return EDGE_API_URL;
}

function e2eUpstreamBlocked(){
  return process.env.RIVEXIS_E2E_BLOCK_EXTERNAL_UPSTREAM==="1";
}

function containsSampleAddress(value:unknown):boolean{
  if(typeof value==="string")return SAMPLE_EVM_ADDRESSES.has(value.trim().toLowerCase());
  if(Array.isArray(value))return value.some(containsSampleAddress);
  if(value&&typeof value==="object")return Object.values(value as Record<string,unknown>).some(containsSampleAddress);
  return false;
}

async function sampleAnalysisRejection(request:Request,path:string,body:Uint8Array|undefined){
  if(request.method.toUpperCase()!=="POST"||!path.startsWith("/api/v1/analysis/"))return null;
  try{
    const payload=JSON.parse(new TextDecoder().decode(body)) as {demo?:unknown;input?:unknown};
    if(payload?.demo===false&&containsSampleAddress(payload.input)){
      return new Response(JSON.stringify({detail:"Replace the sample EVM addresses before submitting a non-demo analysis request."}),{
        status:422,
        headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"},
      });
    }
  }catch{
    // Preserve the upstream's canonical malformed-body handling.
  }
  return null;
}

export async function proxyEdgeApi(request:Request,path:string){
  const method=request.method.toUpperCase();
  if(WRITE_METHODS.has(method)&&!writeOriginAllowed(request))return rejection(403,"Cross-site changes are not allowed");
  const body=method==="GET"||method==="HEAD"?undefined:await boundedBody(request);
  if(body instanceof Response)return body;
  const sampleRejection=await sampleAnalysisRejection(request,path,body);
  if(sampleRejection)return sampleRejection;
  if(e2eUpstreamBlocked()){
    return new Response(JSON.stringify({detail:"External API upstream disabled in local E2E"}),{
      status:503,
      headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"},
    });
  }
  const source=new URL(request.url);
  const target=new URL(`${upstreamBase(path)}${path}`);
  target.search=source.search;
  const headers=new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");
  headers.set("x-rivexis-forwarded-origin",source.origin);
  const upstream=await fetch(target,{method,headers,body,redirect:"manual"});
  const responseHeaders=new Headers(upstream.headers);
  responseHeaders.delete("content-length");
  responseHeaders.delete("content-encoding");
  responseHeaders.set("cache-control","no-store");
  return new Response(upstream.body,{status:upstream.status,statusText:upstream.statusText,headers:responseHeaders});
}
