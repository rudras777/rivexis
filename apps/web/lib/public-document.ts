import {BASE_SECURITY_HEADERS} from './security-headers.mjs';
export const PUBLIC_DOCUMENT_ASSET='/_rivexis-public/landing.html';
type Assets={fetch(request:Request):Promise<Response>};

// Only the public, identity-independent landing document is generated at build
// time. API, account pages and Flight navigation keep the framework handler.
export async function publicDocument(request:Request,assets:Assets):Promise<Response|null>{
 const url=new URL(request.url);
 if(url.pathname!=='/'||!['GET','HEAD'].includes(request.method))return null;
 if(url.searchParams.has('_rsc')||request.headers.has('rsc')||request.headers.has('next-router-state-tree')||request.headers.has('next-router-prefetch')||request.headers.get('accept')?.includes('text/x-component'))return null;
 const headers=new Headers(BASE_SECURITY_HEADERS);
 headers.set('cache-control','public, max-age=0, must-revalidate');
 headers.set('content-type','text/html; charset=utf-8');
 headers.set('vary','RSC, Next-Router-State-Tree, Next-Router-Prefetch, Accept');
 headers.set('x-rivexis-document','build');
 try{
  const target=new URL(PUBLIC_DOCUMENT_ASSET,url.origin);
  // Never pass a session, authorization, conditional or visitor header into the
  // build artifact request. The document contains no account data or cookies.
  const asset=await assets.fetch(new Request(target,{method:request.method}));
  if(asset.status!==200)throw new Error('Public build document unavailable');
  return new Response(request.method==='HEAD'?null:asset.body,{status:200,headers});
 }catch{
  headers.set('cache-control','no-store');headers.delete('x-rivexis-document');
  return new Response(request.method==='HEAD'?null:'The public page is temporarily unavailable. Please try again.',{status:503,headers});
 }
}
