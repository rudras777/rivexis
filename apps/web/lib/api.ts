const configuredApi=process.env.NEXT_PUBLIC_RIVEXIS_API_URL;
export const API=configuredApi==="same-origin"
 ? ""
 : configuredApi??(process.env.NODE_ENV==="production"?"":"http://localhost:8000");
export type EngineId="B1"|"B2"|"B3"|"B4"|"B5"|"F1"|"F2"|"F3"|"F4"|"F5";

export class ApiError extends Error{
 readonly status:number;
 constructor(status:number,message:string){
  super(message);
  this.name="ApiError";
  this.status=status;
 }
}

export function activeWorkspaceId(){return typeof window!=="undefined"?localStorage.getItem("rivexis_workspace_id"):null}
export function setActiveWorkspaceId(id:string){if(typeof window!=="undefined")localStorage.setItem("rivexis_workspace_id",id)}
export function clearActiveWorkspaceId(){if(typeof window!=="undefined")localStorage.removeItem("rivexis_workspace_id")}

let csrfToken:string|null=null;
export function setCsrfToken(token:string|null){csrfToken=token}
const UNSAFE=new Set(["POST","PUT","PATCH","DELETE"]);
const AUTH_CSRF_EXEMPT=new Set([
 "/api/v1/auth/web/login",
 "/api/v1/auth/web/signup",
 "/api/v1/auth/email-verification/request",
 "/api/v1/auth/email-verification/confirm",
 "/api/v1/auth/password-reset/request",
 "/api/v1/auth/password-reset/confirm",
]);

async function responseError(r:Response):Promise<ApiError>{
 let msg=`Request failed (${r.status})`;
 try{
  const j=await r.json() as {detail?:string};
  if(typeof j.detail==="string"&&j.detail.trim())msg=j.detail;
 }catch{}
 return new ApiError(r.status,msg);
}

// One deadline covers CSRF recovery, response headers and the entire body.
// Writes are never retried: a lost response cannot prove the server did not save.
export const API_REQUEST_TIMEOUT_MS=35_000;
async function boundedRequest<T>(init:RequestInit,run:(signal:AbortSignal,markWrite:()=>void)=>Promise<T>):Promise<T>{
 const controller=new AbortController();
 const cancel=()=>controller.abort(init.signal?.reason);
 if(init.signal?.aborted)cancel();else init.signal?.addEventListener("abort",cancel,{once:true});
 let writeStarted=false;
 const timer=setTimeout(()=>controller.abort(new DOMException("Request deadline exceeded","TimeoutError")),API_REQUEST_TIMEOUT_MS);
 try{
  controller.signal.throwIfAborted();
  return await run(controller.signal,()=>{writeStarted=true});
 }catch(cause){
  if(controller.signal.aborted&&controller.signal.reason?.name==="TimeoutError")throw new ApiError(504,writeStarted
   ?"The request timed out and its outcome could not be confirmed. Check the saved record or current settings before retrying."
   :"The request timed out. Try again when the service is available.");
  throw cause;
 }finally{clearTimeout(timer);init.signal?.removeEventListener("abort",cancel)}
}

async function ensureCsrfToken(signal:AbortSignal):Promise<string>{
 if(csrfToken)return csrfToken;
 const r=await fetch(`${API}/api/v1/auth/web/csrf`,{credentials:"include",cache:"no-store",signal});
 if(!r.ok)throw await responseError(r);
 const body=await r.json() as {csrf_token:string};
 if(typeof body.csrf_token!=="string"||!body.csrf_token.trim())throw new ApiError(503,"Session verification is unavailable. Log in again before saving changes.");
 signal.throwIfAborted();
 csrfToken=body.csrf_token;
 return csrfToken;
}

export async function api<T>(path:string,init:RequestInit={}):Promise<T>{
 return boundedRequest(init,async(signal,markWrite)=>{
 const method=(init.method??"GET").toUpperCase();
 const headers=new Headers(init.headers);
 if(init.body!=null&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");
 if(UNSAFE.has(method)&&!AUTH_CSRF_EXEMPT.has(path))headers.set("X-Rivexis-CSRF",await ensureCsrfToken(signal));
 signal.throwIfAborted();
 if(UNSAFE.has(method))markWrite();
 const r=await fetch(`${API}${path}`,{...init,signal,headers,credentials:"include",cache:"no-store"});
 if(!r.ok)throw await responseError(r);
 if(r.status===204)return undefined as T;
 return await r.json() as T;
 });
}

export const enginePath:Record<EngineId,string>={B1:"simulations",B2:"security",B3:"monitoring",B4:"entities",B5:"routes",F1:"portfolio",F2:"protocol-risk",F3:"position-risk",F4:"yield",F5:"treasury"};

export async function apiBlob(path:string,init:RequestInit={}):Promise<Blob>{
 return boundedRequest(init,async(signal,markWrite)=>{
 const method=(init.method??"GET").toUpperCase();
 const headers=new Headers(init.headers);
 if(init.body!=null&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");
 if(UNSAFE.has(method))headers.set("X-Rivexis-CSRF",await ensureCsrfToken(signal));
 signal.throwIfAborted();
 if(UNSAFE.has(method))markWrite();
 const r=await fetch(`${API}${path}`,{...init,signal,headers,credentials:"include",cache:"no-store"});
 if(!r.ok)throw await responseError(r);
 return await r.blob();
 });
}
