import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient,type User} from "npm:@supabase/supabase-js@2";

type Json=Record<string,unknown>;
type SessionCookie={access_token:string;refresh_token:string;csrf:string};
type AuthContext={user:User;session:SessionCookie;cookie?:string};

const SUPABASE_URL=Deno.env.get("SUPABASE_URL")!;
const ANON_KEY=Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_KEY=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const LIVE_ORIGIN="https://rivexis-web.rudrasingh0718.workers.dev";
const COOKIE="rvx_session";
const admin=createClient(SUPABASE_URL,SERVICE_KEY,{auth:{persistSession:false,autoRefreshToken:false}});

function cors(req:Request){
  const origin=req.headers.get("origin");
  const allowed=origin===LIVE_ORIGIN||origin?.startsWith("http://localhost:")||origin?.startsWith("http://127.0.0.1:");
  return {
    "access-control-allow-origin":allowed?origin!:LIVE_ORIGIN,
    "access-control-allow-credentials":"true",
    "access-control-allow-headers":"content-type,x-rivexis-csrf,x-request-id",
    "access-control-allow-methods":"GET,POST,PATCH,OPTIONS",
    "vary":"Origin",
  };
}
function json(req:Request,body:unknown,status=200,cookie?:string){
  const headers=new Headers({...cors(req),"content-type":"application/json; charset=utf-8","cache-control":"no-store"});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(JSON.stringify(body),{status,headers});
}
function error(req:Request,status:number,detail:string,cookie?:string){return json(req,{detail},status,cookie)}
function encode(value:unknown){return btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(value)))).replaceAll("+","-").replaceAll("/","_").replaceAll("=","")}
function decode<T>(value:string):T|null{
  try{
    const normalized=value.replaceAll("-","+").replaceAll("_","/").padEnd(Math.ceil(value.length/4)*4,"=");
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(normalized),c=>c.charCodeAt(0)))) as T;
  }catch{return null}
}
function cookieValue(req:Request,name:string){
  for(const part of (req.headers.get("cookie")??"").split(";")){const [key,...rest]=part.trim().split("=");if(key===name)return rest.join("=")}
  return null;
}
function sessionCookie(session:SessionCookie,maxAge=60*60*24*30){return `${COOKIE}=${encode(session)}; Path=/; Max-Age=${maxAge}; HttpOnly; Secure; SameSite=Lax`}
function clearCookie(){return `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`}

async function authenticate(req:Request):Promise<AuthContext|null>{
  const raw=cookieValue(req,COOKIE);const stored=raw?decode<SessionCookie>(raw):null;
  if(!stored?.access_token||!stored.refresh_token||!stored.csrf)return null;
  const auth=createClient(SUPABASE_URL,ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false}});
  let access=stored.access_token;let refresh=stored.refresh_token;let refreshed=false;
  let {data:{user}}=await auth.auth.getUser(access);
  if(!user){
    const {data,error}=await auth.auth.refreshSession({refresh_token:refresh});
    if(error||!data.user||!data.session)return null;
    user=data.user;access=data.session.access_token;refresh=data.session.refresh_token;refreshed=true;
  }
  const session={access_token:access,refresh_token:refresh,csrf:stored.csrf};
  return {user,session,cookie:refreshed?sessionCookie(session):undefined};
}
function requireCsrf(req:Request,auth:AuthContext){return req.headers.get("x-rivexis-csrf")===auth.session.csrf}
async function alertBridge(action:string,userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_alerts",{p_action:action,p_actor_user_id:userId,p_payload:payload});
  if(error)throw new Error(error.message);
  return data;
}
async function deliveryRuntime():Promise<Record<string,unknown>>{
  const {data,error}=await admin.rpc("rivexis_edge_alert_delivery_runtime");
  if(error||!data||typeof data!=="object"){
    return {processor_status:"NOT_CONFIGURED",sink_status:"NOT_CONFIGURED",recipient_policy:"WORKSPACE_OWNER_EMAIL"};
  }
  return {...data,recipient_policy:"WORKSPACE_OWNER_EMAIL"};
}
function bridgeFailure(req:Request,cause:unknown,cookie?:string){
  const detail=cause instanceof Error?cause.message:"Alert request failed";const normalized=detail.toLowerCase();
  if(normalized.includes("management access required"))return error(req,403,"Workspace management access required",cookie);
  if(normalized.includes("write access required"))return error(req,403,"Workspace write access required",cookie);
  if(normalized.includes("workspace not found")||normalized.includes("alert not found"))return error(req,404,"Alert or workspace not found",cookie);
  if(normalized.includes("invalid alert status"))return error(req,422,"Invalid alert status",cookie);
  if(normalized.includes("only failed alert deliveries can be requeued"))return error(req,409,"Only failed alert deliveries can be requeued",cookie);
  return error(req,500,"Rivexis could not complete the alert request safely",cookie);
}

Deno.serve(async(req:Request)=>{
  if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors(req)});
  const url=new URL(req.url);const marker="/rivexis-alerts";const position=url.pathname.indexOf(marker);const path=position>=0?url.pathname.slice(position+marker.length)||"/":url.pathname;
  if(path==="/health"){
    const runtime=await deliveryRuntime();
    return json(req,{
      status:"ready",service:"rivexis-alerts",runtime:"supabase-edge",api_version:"v1",environment:"production",
      ingestion:"durable-records-only",continuous_threat_ingestion:false,
      delivery_processor:runtime.processor_status,delivery_sink:runtime.sink_status,
      recipient_policy:runtime.recipient_policy,last_delivery_cycle_at:runtime.last_run_at??null,
    });
  }
  const auth=await authenticate(req);
  if(!auth)return error(req,401,"Authentication required",clearCookie());
  const method=req.method.toUpperCase();
  if((method==="POST"||method==="PATCH")&&!requireCsrf(req,auth))return error(req,403,"CSRF validation failed",auth.cookie);
  try{
    if(path==="/api/v1/alerts"&&method==="GET"){
      const workspaceId=url.searchParams.get("workspace_id")??"";
      const [listed,runtime]=await Promise.all([alertBridge("list",auth.user.id,{workspace_id:workspaceId}),deliveryRuntime()]);
      return json(req,{
        ...listed,
        status:`durable_alert_records_only; continuous_threat_stream_not_configured; delivery_processor=${String(runtime.processor_status??"NOT_CONFIGURED").toLowerCase()}`,
      },200,auth.cookie);
    }
    if(path==="/api/v1/alerts/delivery-metrics"&&method==="GET"){
      const workspaceId=url.searchParams.get("workspace_id")??"";
      const raw=Number(url.searchParams.get("slo_seconds")??300);const slo=Number.isFinite(raw)?Math.max(1,Math.min(86400,Math.trunc(raw))):300;
      const [metrics,runtime]=await Promise.all([alertBridge("metrics",auth.user.id,{workspace_id:workspaceId,slo_seconds:slo}),deliveryRuntime()]);
      return json(req,{...metrics,...runtime,recipient_policy:"WORKSPACE_OWNER_EMAIL"},200,auth.cookie);
    }
    const requeue=path.match(/^\/api\/v1\/alerts\/([^/]+)\/requeue$/);
    if(requeue&&method==="POST")return json(req,await alertBridge("requeue",auth.user.id,{alert_id:decodeURIComponent(requeue[1])}),200,auth.cookie);
    const detail=path.match(/^\/api\/v1\/alerts\/([^/]+)$/);
    if(detail&&method==="PATCH"){
      const status=(url.searchParams.get("status")??"").toLowerCase();
      return json(req,await alertBridge("status",auth.user.id,{alert_id:decodeURIComponent(detail[1]),status}),200,auth.cookie);
    }
    return error(req,404,"Not found",auth.cookie);
  }catch(cause){return bridgeFailure(req,cause,auth.cookie)}
});
