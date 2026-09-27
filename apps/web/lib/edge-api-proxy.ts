const EDGE_API_URL="https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-api";

export async function proxyEdgeApi(request:Request,path:string){
  const source=new URL(request.url);
  const target=new URL(`${EDGE_API_URL}${path}`);
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
