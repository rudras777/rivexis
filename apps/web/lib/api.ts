export const API=process.env.NEXT_PUBLIC_RIVEXIS_API_URL ?? "http://localhost:8000";
export type EngineId="B1"|"B2"|"B3"|"B4"|"B5"|"F1"|"F2"|"F3"|"F4"|"F5";
export function activeWorkspaceId(){return typeof window!=="undefined"?localStorage.getItem("rivexis_workspace_id"):null}
export function setActiveWorkspaceId(id:string){if(typeof window!=="undefined")localStorage.setItem("rivexis_workspace_id",id)}

let csrfToken:string|null=null;
export function setCsrfToken(token:string|null){csrfToken=token}
const UNSAFE=new Set(["POST","PUT","PATCH","DELETE"]);
function webAuthBootstrap(path:string){return path==="/api/v1/auth/web/login"||path==="/api/v1/auth/web/signup"}
async function ensureCsrfToken():Promise<string>{
 if(csrfToken)return csrfToken;
 const r=await fetch(`${API}/api/v1/auth/web/csrf`,{credentials:"include",cache:"no-store"});
 if(!r.ok)throw new Error("Session CSRF initialization failed");
 const body=await r.json() as {csrf_token:string};csrfToken=body.csrf_token;return csrfToken;
}
export async function api<T>(path:string,init:RequestInit={}):Promise<T>{
 const method=(init.method??"GET").toUpperCase();
 const headers=new Headers(init.headers);
 if(init.body!=null&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");
 if(UNSAFE.has(method)&&!webAuthBootstrap(path))headers.set("X-Rivexis-CSRF",await ensureCsrfToken());
 const r=await fetch(`${API}${path}`,{...init,headers,credentials:"include",cache:"no-store"});
 if(!r.ok){let msg=`Request failed (${r.status})`;try{const j=await r.json() as {detail?:string};msg=j.detail??msg}catch{};throw new Error(msg)}
 if(r.status===204)return undefined as T;return r.json() as Promise<T>;
}
export const enginePath:Record<EngineId,string>={B1:"simulations",B2:"security",B3:"monitoring",B4:"entities",B5:"routes",F1:"portfolio",F2:"protocol-risk",F3:"position-risk",F4:"yield",F5:"treasury"};
export async function apiBlob(path:string,init:RequestInit={}):Promise<Blob>{
 const method=(init.method??"GET").toUpperCase();
 const headers=new Headers(init.headers);
 if(UNSAFE.has(method))headers.set("X-Rivexis-CSRF",await ensureCsrfToken());
 const r=await fetch(`${API}${path}`,{...init,headers,credentials:"include",cache:"no-store"});
 if(!r.ok){let msg=`Request failed (${r.status})`;try{const j=await r.json() as {detail?:string};msg=j.detail??msg}catch{};throw new Error(msg)}
 return r.blob();
}
