import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient,type User} from "npm:@supabase/supabase-js@2";
import {analyzeCanonicalDecision,decisionReportHtml,decisionReportLines} from "../rivexis-api/decision-report.mjs";

type Json=Record<string,unknown>;
type SessionCookie={access_token:string;refresh_token:string;csrf:string};
type AuthContext={user:User;session:SessionCookie;cookie?:string};

const SUPABASE_URL=Deno.env.get("SUPABASE_URL")!;
const ANON_KEY=Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_KEY=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const LIVE_ORIGIN="https://rivexis-web.rudrasingh0718.workers.dev";
const COOKIE="rvx_session";
const admin=createClient(SUPABASE_URL,SERVICE_KEY,{auth:{persistSession:false,autoRefreshToken:false}});

async function decisionBridge(action:string,userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_decision_report",{p_action:action,p_actor_user_id:userId,p_payload:payload});
  if(error)throw new Error(error.message);
  return data;
}

function cors(req:Request){
  const origin=req.headers.get("origin");
  const allowed=origin===LIVE_ORIGIN||origin?.startsWith("http://localhost:")||origin?.startsWith("http://127.0.0.1:");
  return {
    "access-control-allow-origin":allowed?origin!:LIVE_ORIGIN,
    "access-control-allow-credentials":"true",
    "access-control-allow-headers":"content-type,x-rivexis-csrf,x-request-id",
    "access-control-allow-methods":"GET,POST,OPTIONS",
    "vary":"Origin",
  };
}

function json(req:Request,value:unknown,status=200,cookie?:string,extra:Record<string,string>={}){
  const headers=new Headers({...cors(req),"content-type":"application/json; charset=utf-8","cache-control":"no-store",...extra});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(JSON.stringify(value),{status,headers});
}
function text(req:Request,value:string,contentType:string,cookie?:string,extra:Record<string,string>={}){
  const headers=new Headers({...cors(req),"content-type":contentType,"cache-control":"no-store",...extra});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(value,{status:200,headers});
}
function binary(req:Request,value:Uint8Array,filename:string,cookie?:string,extra:Record<string,string>={}){
  const headers=new Headers({...cors(req),"content-type":"application/pdf","cache-control":"no-store","content-disposition":`inline; filename="${filename}"`,...extra});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(value,{status:200,headers});
}
function fail(req:Request,status:number,detail:string,cookie?:string){return json(req,{detail},status,cookie)}

function encode(value:unknown){return btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(value)))).replaceAll("+","-").replaceAll("/","_").replaceAll("=","")}
function decode<T>(value:string):T|null{
  try{const normalized=value.replaceAll("-","+").replaceAll("_","/").padEnd(Math.ceil(value.length/4)*4,"=");return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(normalized),c=>c.charCodeAt(0)))) as T}catch{return null}
}
function cookieValue(req:Request,name:string){for(const part of (req.headers.get("cookie")??"").split(";")){const [key,...rest]=part.trim().split("=");if(key===name)return rest.join("=")}return null}
function sessionCookie(session:SessionCookie,maxAge=60*60*24*30){return `${COOKIE}=${encode(session)}; Path=/; Max-Age=${maxAge}; HttpOnly; Secure; SameSite=Lax`}
function clearCookie(){return `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`}
async function requestBody(req:Request):Promise<Json>{try{const value=await req.json();return value&&typeof value==="object"&&!Array.isArray(value)?value as Json:{}}catch{return {}}}

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

function bridgeFailure(req:Request,cause:unknown,cookie?:string){
  const detail=cause instanceof Error?cause.message:"Decision/report request failed";
  const normalized=detail.toLowerCase();
  if(normalized.includes("write access"))return fail(req,403,detail,cookie);
  if(normalized.includes("unavailable")||normalized.includes("not found"))return fail(req,404,detail,cookie);
  if(normalized.includes("different workspaces"))return fail(req,409,detail,cookie);
  if(normalized.includes("at least one")||normalized.includes("invalid decision")||normalized.includes("supports html"))return fail(req,422,detail,cookie);
  return fail(req,500,"Rivexis could not complete the decision/report request safely",cookie);
}

function minimalPdf(title:string,lines:string[]){
  const clean=(value:string)=>value.replaceAll("\\","\\\\").replaceAll("(","\\(").replaceAll(")","\\)").replaceAll(/[^\x20-\x7E]/g,"?");
  const content=["BT","/F1 16 Tf","72 760 Td",`(${clean(title)}) Tj`,"/F1 10 Tf",...lines.slice(0,28).flatMap(line=>["0 -18 Td",`(${clean(line)}) Tj`]),"ET"].join("\n");
  const objects=["1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj","2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj","3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj","4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",`5 0 obj << /Length ${new TextEncoder().encode(content).length} >> stream\n${content}\nendstream endobj`];
  let pdf="%PDF-1.4\n";const offsets=[0];for(const object of objects){offsets.push(new TextEncoder().encode(pdf).length);pdf+=object+"\n"}
  const xref=new TextEncoder().encode(pdf).length;pdf+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n${offsets.slice(1).map(offset=>`${String(offset).padStart(10,"0")} 00000 n `).join("\n")}\ntrailer << /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return new TextEncoder().encode(pdf);
}

async function handle(req:Request,path:string,url:URL,auth:AuthContext){
  const method=req.method.toUpperCase();
  if(method==="POST"&&req.headers.get("x-rivexis-csrf")!==auth.session.csrf)return fail(req,403,"CSRF validation failed",auth.cookie);

  if(path==="/api/v1/decisions/analyze"&&method==="POST"){
    const input=await requestBody(req);
    const submitted=Array.isArray(input.engine_results)?input.engine_results:[];
    const analysisIds=submitted.map(item=>item&&typeof item==="object"&&"analysis_id" in item?String((item as Json).analysis_id??""):"");
    if(!analysisIds.length||analysisIds.some(value=>!value))return fail(req,422,"At least one persisted engine result is required",auth.cookie);
    try{
      const canonical=await decisionBridge("decision_inputs",auth.user.id,{analysis_ids:analysisIds});
      const decision=analyzeCanonicalDecision(canonical.items??[]);
      await decisionBridge("save_decision",auth.user.id,{workspace_id:canonical.workspace_id,decision});
      return json(req,decision,200,auth.cookie);
    }catch(cause){return bridgeFailure(req,cause,auth.cookie)}
  }

  const decisionDetail=path.match(/^\/api\/v1\/decisions\/([^/]+)$/);
  if(decisionDetail&&method==="GET"){
    try{return json(req,await decisionBridge("get_decision",auth.user.id,{decision_id:decodeURIComponent(decisionDetail[1])}),200,auth.cookie)}catch(cause){return bridgeFailure(req,cause,auth.cookie)}
  }

  if(path==="/api/v1/history"&&method==="GET"){
    const workspaceId=url.searchParams.get("workspace_id")??"";const limit=Math.max(1,Math.min(200,Number(url.searchParams.get("limit")??50)));
    try{return json(req,await decisionBridge("history",auth.user.id,{workspace_id:workspaceId,limit}),200,auth.cookie)}catch(cause){return bridgeFailure(req,cause,auth.cookie)}
  }

  if(path==="/api/v1/reports"&&method==="POST"){
    const input=await requestBody(req);const decisionId=typeof input.decision_id==="string"?input.decision_id.trim():"";const format=typeof input.format==="string"?input.format.toLowerCase():"html";
    if(!decisionId||!["html","pdf","json"].includes(format))return fail(req,422,"MVP supports html, pdf and json",auth.cookie);
    try{
      const decision=await decisionBridge("get_decision",auth.user.id,{decision_id:decisionId});
      const report=await decisionBridge("create_report",auth.user.id,{decision_id:decisionId,format});
      const headers={"x-rivexis-report-id":String(report.id)};
      if(format==="json")return json(req,{report_id:report.id,report},200,auth.cookie,headers);
      if(format==="html")return text(req,decisionReportHtml(decision),"text/html; charset=utf-8",auth.cookie,headers);
      return binary(req,minimalPdf("RIVEXIS Decision Report",decisionReportLines(decision)),`rivexis-${report.id}.pdf`,auth.cookie,headers);
    }catch(cause){return bridgeFailure(req,cause,auth.cookie)}
  }

  const reportDetail=path.match(/^\/api\/v1\/reports\/([^/]+)$/);
  if(reportDetail&&method==="GET"){
    try{return json(req,await decisionBridge("get_report",auth.user.id,{report_id:decodeURIComponent(reportDetail[1])}),200,auth.cookie)}catch(cause){return bridgeFailure(req,cause,auth.cookie)}
  }

  return fail(req,404,"Not found",auth.cookie);
}

Deno.serve(async(req:Request)=>{
  if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors(req)});
  const url=new URL(req.url);const marker="/rivexis-decision-reports";const position=url.pathname.indexOf(marker);const path=position>=0?url.pathname.slice(position+marker.length)||"/":url.pathname;
  if(path==="/health")return json(req,{status:"ready",service:"rivexis-decision-reports",runtime:"supabase-edge",api_version:"v1",environment:"production"});
  const auth=await authenticate(req);if(!auth)return fail(req,401,"Authentication required",clearCookie());
  try{return await handle(req,path,url,auth)}catch(cause){console.error("rivexis decision/report request failed",cause instanceof Error?cause.message:JSON.stringify(cause));return fail(req,500,"Rivexis could not complete the request safely",auth.cookie)}
});
