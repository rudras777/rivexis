const EDGE_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-api";
const DECISION_REPORT_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-decision-reports";
const ALERTS_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-alerts";

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

async function sampleAnalysisRejection(request:Request,path:string){
  if(request.method.toUpperCase()!=="POST"||!path.startsWith("/api/v1/analysis/"))return null;
  try{
    const payload=await request.clone().json() as {demo?:unknown;input?:unknown};
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
  const sampleRejection=await sampleAnalysisRejection(request,path);
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
  const method=request.method.toUpperCase();
  const upstream=await fetch(target,{method,headers,body:method==="GET"||method==="HEAD"?undefined:request.body,redirect:"manual"});
  const responseHeaders=new Headers(upstream.headers);
  responseHeaders.delete("content-length");
  responseHeaders.delete("content-encoding");
  responseHeaders.set("cache-control","no-store");
  return new Response(upstream.body,{status:upstream.status,statusText:upstream.statusText,headers:responseHeaders});
}
