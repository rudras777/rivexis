import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient, type SupabaseClient, type User} from "npm:@supabase/supabase-js@2";
import {analysisResult} from "./analysis.mjs";

type Json=Record<string,unknown>;
type SessionCookie={access_token:string;refresh_token:string;csrf:string};
type AuthContext={user:User;appUser:Json;session:SessionCookie;cookie?:string};

const SUPABASE_URL=Deno.env.get("SUPABASE_URL")!;
const ANON_KEY=Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_KEY=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const LIVE_ORIGIN="https://rivexis-web.rudrasingh0718.workers.dev";
const COOKIE="rvx_session";
const ROLES=new Set(["Individual","Fund","Treasury","Analyst"]);
const ENGINE_PATHS:Record<string,string>={
  simulations:"B1",security:"B2",monitoring:"B3",entities:"B4",routes:"B5",
  portfolio:"F1","protocol-risk":"F2","position-risk":"F3",yield:"F4",treasury:"F5",
};
const PROVIDERS=["direct_rpc","alchemy","quicknode","tenderly","etherscan","blockaid","nansen","arkham","coingecko","defillama","lifi","defillama_yields"];

const admin=createClient(SUPABASE_URL,SERVICE_KEY,{auth:{persistSession:false,autoRefreshToken:false}});

async function bridge(action:string,userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_bridge",{p_action:action,p_actor_user_id:userId,p_payload:payload});
  if(error)throw new Error(error.message);
  return data;
}

async function savedBridge(action:string,userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_saved_analysis",{p_action:action,p_actor_user_id:userId,p_payload:payload});
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
    "access-control-allow-methods":"GET,POST,PATCH,PUT,DELETE,OPTIONS",
    "vary":"Origin",
  };
}

function json(req:Request,body:unknown,status=200,cookie?:string){
  const headers=new Headers({...cors(req),"content-type":"application/json; charset=utf-8","cache-control":"no-store"});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(JSON.stringify(body),{status,headers});
}

function empty(req:Request,status=204,cookie?:string){
  const headers=new Headers({...cors(req),"cache-control":"no-store"});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(null,{status,headers});
}

function binary(req:Request,body:Uint8Array,contentType:string,filename:string,cookie?:string){
  const headers=new Headers({...cors(req),"content-type":contentType,"cache-control":"no-store","content-disposition":`inline; filename="${filename}"`});
  if(cookie)headers.set("set-cookie",cookie);
  return new Response(body,{status:200,headers});
}

function error(req:Request,status:number,detail:string,cookie?:string){return json(req,{detail},status,cookie)}
function now(){return new Date().toISOString()}
function id(){return crypto.randomUUID()}
function encode(value:unknown){return btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(value)))).replaceAll("+","-").replaceAll("/","_").replaceAll("=","")}
function decode<T>(value:string):T|null{
  try{
    const normalized=value.replaceAll("-","+").replaceAll("_","/").padEnd(Math.ceil(value.length/4)*4,"=");
    return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(normalized),c=>c.charCodeAt(0)))) as T;
  }catch{return null}
}
function cookieValue(req:Request,name:string){
  const raw=req.headers.get("cookie")??"";
  for(const part of raw.split(";")){const [key,...rest]=part.trim().split("=");if(key===name)return rest.join("=")}
  return null;
}
function sessionCookie(session:SessionCookie,maxAge=60*60*24*30){
  return `${COOKIE}=${encode(session)}; Path=/; Max-Age=${maxAge}; HttpOnly; Secure; SameSite=Lax`;
}
function clearCookie(){return `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`}
function role(value:unknown){return typeof value==="string"&&ROLES.has(value)?value:"Individual"}
async function body(req:Request):Promise<Json>{
  try{const value=await req.json();return value&&typeof value==="object"&&!Array.isArray(value)?value as Json:{}}catch{return {}}
}

async function ensureAppUser(user:User){
  return await bridge("ensure_user",user.id,{email:(user.email??"").toLowerCase(),role:role(user.user_metadata?.role)}) as Json;
}

async function authenticate(req:Request):Promise<AuthContext|null>{
  const value=cookieValue(req,COOKIE);
  const stored=value?decode<SessionCookie>(value):null;
  if(!stored?.access_token||!stored.refresh_token||!stored.csrf)return null;
  const auth=createClient(SUPABASE_URL,ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false}});
  let access=stored.access_token;
  let refresh=stored.refresh_token;
  let refreshed=false;
  let {data:{user}}=await auth.auth.getUser(access);
  if(!user){
    const {data,error}=await auth.auth.refreshSession({refresh_token:refresh});
    if(error||!data.user||!data.session)return null;
    user=data.user;access=data.session.access_token;refresh=data.session.refresh_token;refreshed=true;
  }
  const next={access_token:access,refresh_token:refresh,csrf:stored.csrf};
  return {user,appUser:await ensureAppUser(user),session:next,cookie:refreshed?sessionCookie(next):undefined};
}

function requireCsrf(req:Request,auth:AuthContext){
  return req.headers.get("x-rivexis-csrf")===auth.session.csrf;
}

async function personalWorkspaces(userId:string){
  return ((await bridge("list_workspaces",userId))?.items??[]).filter((row:any)=>row.organization_id==null);
}

async function organizationWorkspaces(userId:string){
  return ((await bridge("list_workspaces",userId))?.items??[]).filter((row:any)=>row.organization_id!=null);
}

async function allWorkspaces(userId:string){return (await bridge("list_workspaces",userId))?.items??[]}
async function workspaceAccess(userId:string,workspaceId:string,write=false){
  const rows=await allWorkspaces(userId);
  const row=rows.find(item=>item.id===workspaceId)??null;
  if(!row)return null;
  if(write&&!new Set(["OWNER","ADMIN","ANALYST"]).has(row.access_role))return null;
  return row;
}

async function handleAuth(req:Request,path:string){
  const input=await body(req);
  const authClient=createClient(SUPABASE_URL,ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false}});
  if(path==="/api/v1/auth/web/login"){
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    const password=typeof input.password==="string"?input.password:"";
    if(!email||password.length<8)return error(req,422,"Email and password are required");
    const {data,error:signInError}=await authClient.auth.signInWithPassword({email,password});
    if(signInError||!data.user||!data.session)return error(req,signInError?.message.toLowerCase().includes("confirm")?403:401,signInError?.message.toLowerCase().includes("confirm")?"Email verification is required before login":"Invalid credentials");
    const appUser=await ensureAppUser(data.user);
    const session={access_token:data.session.access_token,refresh_token:data.session.refresh_token,csrf:crypto.randomUUID()};
    return json(req,{csrf_token:session.csrf,user:{id:data.user.id,email:data.user.email,role:appUser.role}},200,sessionCookie(session));
  }
  if(path==="/api/v1/auth/web/signup"){
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    const password=typeof input.password==="string"?input.password:"";
    const userRole=role(input.role);
    if(!email||password.length<8)return error(req,422,"Check your email, password, and role, then try again");
    const {data,error:signUpError}=await authClient.auth.signUp({email,password,options:{data:{role:userRole},emailRedirectTo:`${LIVE_ORIGIN}/login?verified=1`}});
    if(signUpError)return error(req,signUpError.status===429?429:409,"Unable to create account with those details");
    if(data.user&&data.session){
      const appUser=await ensureAppUser(data.user);
      const session={access_token:data.session.access_token,refresh_token:data.session.refresh_token,csrf:crypto.randomUUID()};
      return json(req,{csrf_token:session.csrf,verification_required:false,user:{id:data.user.id,email:data.user.email,role:appUser.role}},200,sessionCookie(session));
    }
    return json(req,{verification_required:true,email_status:"accepted"},200);
  }
  if(path==="/api/v1/auth/email-verification/request"){
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    if(email)await authClient.auth.resend({type:"signup",email,options:{emailRedirectTo:`${LIVE_ORIGIN}/login?verified=1`}});
    return json(req,{status:"accepted"},202);
  }
  if(path==="/api/v1/auth/email-verification/confirm"){
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    const token=typeof input.token==="string"?input.token.trim():"";
    if(!email||!token)return error(req,422,"Email and verification code are required");
    const {error:verifyError}=await authClient.auth.verifyOtp({email,token,type:"signup"});
    if(verifyError)return error(req,400,"This verification code is invalid or expired");
    return json(req,{status:"verified"});
  }
  if(path==="/api/v1/auth/password-reset/request"){
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    if(email)await authClient.auth.resetPasswordForEmail(email,{redirectTo:`${LIVE_ORIGIN}/reset-password`});
    return json(req,{status:"accepted"},202);
  }
  if(path==="/api/v1/auth/password-reset/confirm"){
    const tokenHash=typeof input.token_hash==="string"?input.token_hash.trim():"";
    const token=typeof input.token==="string"?input.token.trim():"";
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    const accessToken=typeof input.access_token==="string"?input.access_token:"";
    const refreshToken=typeof input.refresh_token==="string"?input.refresh_token:"";
    const password=typeof input.password==="string"?input.password:"";
    if(password.length<8)return error(req,422,"Password must contain at least eight characters");
    const verified=accessToken&&refreshToken
      ?await authClient.auth.setSession({access_token:accessToken,refresh_token:refreshToken})
      :tokenHash
        ?await authClient.auth.verifyOtp({token_hash:tokenHash,type:"recovery"})
        :await authClient.auth.verifyOtp({email,token,type:"recovery"});
    if(verified.error||!verified.data.session)return error(req,400,"This recovery link is invalid or expired");
    const updater=createClient(SUPABASE_URL,ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false},global:{headers:{Authorization:`Bearer ${verified.data.session.access_token}`}}});
    const {error:updateError}=await updater.auth.updateUser({password});
    if(updateError)return error(req,400,"Unable to update password");
    return json(req,{status:"updated",sessions_revoked:true});
  }
  return error(req,404,"Not found");
}

function protocolInput(value:unknown){
  const input=value&&typeof value==="object"&&!Array.isArray(value)?value as Json:{};
  const from=Number(input.from_block);const to=Number(input.to_block);
  if(!Number.isSafeInteger(from)||!Number.isSafeInteger(to)||from<0||to<from)throw new Error("INVALID_BLOCK_RANGE");
  return {input,from,to,adapter:String(input.protocol_adapter??"unknown"),chain:String(input.chain??"ethereum")};
}

function unavailableTimeline(value:unknown){
  const {from,to,adapter,chain}=protocolInput(value);
  return {
    adapter,chain,from_block:from,to_block:to,event_count:0,events:[],
    deployment_identity:{verified:false,reason:"NO_VERIFIED_PROVIDER_EVIDENCE"},
    log_fetch:{status:"NOT_CONFIGURED",provider:null},
    warnings:["No archive-capable RPC provider is configured in the free runtime. No event-absence claim was produced."],
    missing_data:["archive-capable RPC logs","verified protocol deployment identity"],
  };
}

function unavailableComparison(value:unknown){
  const {from,to,adapter,chain}=protocolInput(value);
  return {
    adapter,chain,from_block:from,to_block:to,change_count:0,changes:[],materiality_counts:{HIGH:0,MEDIUM:0,LOW:0},
    deployment_identity:{verified:false,reason:"NO_VERIFIED_PROVIDER_EVIDENCE"},
    warnings:["No archive-capable RPC provider is configured. Zero reported changes is not evidence that configuration was unchanged."],
    missing_data:["verified protocol configuration at both requested blocks"],
  };
}

function minimalPdf(title:string,lines:string[]){
  const clean=(value:string)=>value.replaceAll("\\","\\\\").replaceAll("(","\\(").replaceAll(")","\\)").replaceAll(/[^\x20-\x7E]/g,"?");
  const content=["BT","/F1 16 Tf","72 760 Td",`(${clean(title)}) Tj`,"/F1 10 Tf",...lines.slice(0,24).flatMap(line=>["0 -18 Td",`(${clean(line)}) Tj`]),"ET"].join("\n");
  const objects=[
    "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
    "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
    "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
    "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    `5 0 obj << /Length ${new TextEncoder().encode(content).length} >> stream\n${content}\nendstream endobj`,
  ];
  let pdf="%PDF-1.4\n";const offsets=[0];
  for(const object of objects){offsets.push(new TextEncoder().encode(pdf).length);pdf+=object+"\n"}
  const xref=new TextEncoder().encode(pdf).length;
  pdf+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n${offsets.slice(1).map(offset=>`${String(offset).padStart(10,"0")} 00000 n `).join("\n")}\ntrailer << /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return new TextEncoder().encode(pdf);
}

async function persistAnalysis(auth:AuthContext,workspaceId:string,result:Json){
  await bridge("create_analysis",auth.user.id,{workspace_id:workspaceId,analysis_id:result.analysis_id,engine_id:result.engine_id,demo:result.demo,status:result.status,result});
}

async function handleApi(req:Request,path:string,url:URL,auth:AuthContext){
  const method=req.method.toUpperCase();
  const write=["POST","PUT","PATCH","DELETE"].includes(method);
  if(write&&!requireCsrf(req,auth))return error(req,403,"CSRF validation failed",auth.cookie);

  if(path==="/api/v1/auth/web/csrf")return json(req,{csrf_token:auth.session.csrf},200,auth.cookie);
  if(path==="/api/v1/auth/logout"&&method==="POST"){
    const client=createClient(SUPABASE_URL,ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false}});
    await client.auth.setSession({access_token:auth.session.access_token,refresh_token:auth.session.refresh_token});
    await client.auth.signOut({scope:"local"});
    return json(req,{status:"revoked",scope:"current_session"},200,clearCookie());
  }
  if(path==="/api/v1/me"&&method==="GET")return json(req,{id:auth.user.id,email:auth.user.email,role:auth.appUser.role,email_verified:Boolean(auth.user.email_confirmed_at)},200,auth.cookie);
  if(path==="/api/v1/me/role"&&method==="PATCH"){
    const input=await body(req);const nextRole=role(input.role);
    return json(req,await bridge("update_role",auth.user.id,{role:nextRole}),200,auth.cookie);
  }
  if(path==="/api/v1/workspaces"&&method==="GET")return json(req,{items:await allWorkspaces(auth.user.id)},200,auth.cookie);
  if(path==="/api/v1/workspaces"&&method==="POST"){
    const input=await body(req);const name=typeof input.name==="string"?input.name.trim():"";const workspaceRole=role(input.role);
    if(name.length<2)return error(req,422,"Workspace name is required",auth.cookie);
    return json(req,await bridge("create_workspace",auth.user.id,{name,role:workspaceRole}),200,auth.cookie);
  }
  if(path==="/api/v1/organizations"&&method==="GET"){
    return json(req,await bridge("list_organizations",auth.user.id),200,auth.cookie);
  }
  if(path==="/api/v1/organizations"&&method==="POST"){
    const input=await body(req);const name=typeof input.name==="string"?input.name.trim():"";if(name.length<2)return error(req,422,"Organization name is required",auth.cookie);
    return json(req,await bridge("create_organization",auth.user.id,{name}),200,auth.cookie);
  }
  if(path==="/api/v1/history"&&method==="GET"){
    const workspaceId=url.searchParams.get("workspace_id");if(!workspaceId||!await workspaceAccess(auth.user.id,workspaceId))return error(req,404,"Workspace not found",auth.cookie);
    const limit=Math.max(1,Math.min(200,Number(url.searchParams.get("limit")??50)));
    return json(req,await bridge("history",auth.user.id,{workspace_id:workspaceId,limit}),200,auth.cookie);
  }
  const analysisDetail=path.match(/^\/api\/v1\/analyses\/([^/]+)$/);
  if(analysisDetail&&method==="GET"){
    return json(req,await bridge("analysis_detail",auth.user.id,{analysis_id:decodeURIComponent(analysisDetail[1])}),200,auth.cookie);
  }
  if(path==="/api/v1/saved-analyses"&&method==="GET"){
    const workspaceId=url.searchParams.get("workspace_id");if(!workspaceId||!await workspaceAccess(auth.user.id,workspaceId))return error(req,404,"Workspace not found",auth.cookie);
    const includeArchived=url.searchParams.get("include_archived")==="true";
    return json(req,await savedBridge("list",auth.user.id,{workspace_id:workspaceId,include_archived:includeArchived}),200,auth.cookie);
  }
  if(path==="/api/v1/saved-analyses"&&method==="POST"){
    const input=await body(req);
    const analysisId=typeof input.analysis_id==="string"?input.analysis_id.trim():"";
    const title=typeof input.title==="string"?input.title.trim():"";
    if(!analysisId||!title)return error(req,422,"Analysis reference and title are required",auth.cookie);
    const saved=await savedBridge("create",auth.user.id,{analysis_id:analysisId,title});
    if(!saved)return error(req,404,"Analysis not found",auth.cookie);
    return json(req,saved,200,auth.cookie);
  }
  const savedDetail=path.match(/^\/api\/v1\/saved-analyses\/([^/]+)$/);
  if(savedDetail&&method==="PATCH"){
    const archived=url.searchParams.get("archived")!=="false";
    const saved=await savedBridge("archive",auth.user.id,{saved_id:decodeURIComponent(savedDetail[1]),archived});
    if(!saved)return error(req,404,"Saved analysis not found",auth.cookie);
    return json(req,saved,200,auth.cookie);
  }
  if(savedDetail&&method==="DELETE"){
    const outcome=await savedBridge("delete",auth.user.id,{saved_id:decodeURIComponent(savedDetail[1])});
    if(outcome?.deleted!==true)return error(req,404,"Saved analysis not found",auth.cookie);
    return empty(req,204,auth.cookie);
  }
  if(path==="/api/v1/providers/status"&&method==="GET"){
    const chain=url.searchParams.get("chain")??"ethereum";
    return json(req,{chain,deep_probe_available:false,providers:PROVIDERS.map(provider_id=>({provider_id,status:"NOT_CONFIGURED",configured:false,detail:"No production credential is configured in the free runtime"}))},200,auth.cookie);
  }
  if(path==="/api/v1/providers/runtime"&&method==="GET"){
    const workspaceId=url.searchParams.get("workspace_id");if(!workspaceId||!await workspaceAccess(auth.user.id,workspaceId))return error(req,404,"Workspace not found",auth.cookie);
    return json(req,{scope:workspaceId,control_backend:"supabase-edge",providers:{}},200,auth.cookie);
  }
  if(path==="/api/v1/protocol-history/timeline"&&method==="POST"){
    const input=await body(req);const workspaceId=typeof input.workspace_id==="string"?input.workspace_id:"";
    if(!await workspaceAccess(auth.user.id,workspaceId,true))return error(req,403,"Workspace write access required",auth.cookie);
    try{return json(req,unavailableTimeline(input.input),200,auth.cookie)}catch{return error(req,422,"A valid from/to block range is required",auth.cookie)}
  }
  if(path==="/api/v1/protocol-config/compare"&&method==="POST"){
    const input=await body(req);const workspaceId=typeof input.workspace_id==="string"?input.workspace_id:"";
    if(!await workspaceAccess(auth.user.id,workspaceId,true))return error(req,403,"Workspace write access required",auth.cookie);
    try{return json(req,unavailableComparison(input.input),200,auth.cookie)}catch{return error(req,422,"A valid from/to block range is required",auth.cookie)}
  }
  if(path==="/api/v1/protocol-config/reviews"&&method==="POST"){
    const input=await body(req);const workspaceId=typeof input.workspace_id==="string"?input.workspace_id:"";
    if(!await workspaceAccess(auth.user.id,workspaceId,true))return error(req,403,"Workspace write access required",auth.cookie);
    try{
      const review=unavailableComparison(input.input);
      return json(req,await bridge("create_protocol_review",auth.user.id,{workspace_id:workspaceId,payload:review}),200,auth.cookie);
    }catch{return error(req,422,"A valid from/to block range is required",auth.cookie)}
  }
  const reviewApprove=path.match(/^\/api\/v1\/protocol-config\/reviews\/([^/]+)\/approve$/);
  if(reviewApprove&&method==="POST")return json(req,await bridge("approve_protocol_review",auth.user.id,{report_id:decodeURIComponent(reviewApprove[1])}),200,auth.cookie);
  const reviewRender=path.match(/^\/api\/v1\/protocol-config\/reviews\/([^/]+)\/render$/);
  if(reviewRender&&method==="GET"){
    const row=await bridge("get_protocol_review",auth.user.id,{report_id:decodeURIComponent(reviewRender[1])});
    const payload=row.payload??{};
    return binary(req,minimalPdf("RIVEXIS Protocol Configuration Review",[
      `Review: ${row.id}`,`Status: ${row.status}`,`Adapter: ${payload.adapter??"unknown"}`,`Chain: ${payload.chain??"unknown"}`,
      `Blocks: ${payload.from_block??"?"} to ${payload.to_block??"?"}`,"Evidence status: UNKNOWN - no verified archive provider configured.",
    ]),"application/pdf",`rivexis-protocol-review-${row.id}.pdf`,auth.cookie);
  }
  if(path==="/api/v1/protocol-investigations"&&method==="GET"){
    const workspaceId=url.searchParams.get("workspace_id");if(!workspaceId||!await workspaceAccess(auth.user.id,workspaceId))return error(req,404,"Workspace not found",auth.cookie);
    return json(req,await bridge("list_protocol_investigations",auth.user.id,{workspace_id:workspaceId}),200,auth.cookie);
  }
  if(path==="/api/v1/protocol-investigations"&&method==="POST"){
    const input=await body(req);const workspaceId=typeof input.workspace_id==="string"?input.workspace_id:"";const title=typeof input.title==="string"?input.title.trim():"";
    if(!await workspaceAccess(auth.user.id,workspaceId,true))return error(req,403,"Workspace write access required",auth.cookie);
    if(title.length<2)return error(req,422,"Investigation title is required",auth.cookie);
    try{
      const timeline=unavailableTimeline(input.input);
      return json(req,await bridge("create_protocol_investigation",auth.user.id,{workspace_id:workspaceId,title,input:input.input??{},notes:String(input.notes??""),timeline}),200,auth.cookie);
    }catch{return error(req,422,"A valid from/to block range is required",auth.cookie)}
  }
  const investigationAttach=path.match(/^\/api\/v1\/protocol-investigations\/([^/]+)\/reviews\/([^/]+)$/);
  if(investigationAttach&&method==="POST")return json(req,await bridge("attach_protocol_review",auth.user.id,{case_id:decodeURIComponent(investigationAttach[1]),review_id:decodeURIComponent(investigationAttach[2])}),200,auth.cookie);
  const investigationRender=path.match(/^\/api\/v1\/protocol-investigations\/([^/]+)\/render$/);
  if(investigationRender&&method==="GET"){
    const row=await bridge("get_protocol_investigation",auth.user.id,{case_id:decodeURIComponent(investigationRender[1])});const payload=row.payload??{};
    return binary(req,minimalPdf("RIVEXIS Protocol Investigation",[
      `Case: ${row.id}`,`Title: ${payload.title??"Untitled"}`,`Status: ${row.status}`,`Events preserved: ${payload.timeline?.event_count??0}`,
      `Disposition: ${payload.disposition??"Not recorded"}`,"This artifact records analyst workflow; it does not certify protocol safety.",
    ]),"application/pdf",`rivexis-investigation-${row.id}.pdf`,auth.cookie);
  }
  const investigationDetail=path.match(/^\/api\/v1\/protocol-investigations\/([^/]+)$/);
  if(investigationDetail&&method==="GET")return json(req,await bridge("get_protocol_investigation",auth.user.id,{case_id:decodeURIComponent(investigationDetail[1])}),200,auth.cookie);
  if(investigationDetail&&method==="PATCH"){
    const input=await body(req);
    return json(req,await bridge("update_protocol_investigation",auth.user.id,{case_id:decodeURIComponent(investigationDetail[1]),status:input.status,notes:input.notes,disposition:input.disposition}),200,auth.cookie);
  }
  const analysisPath=path.match(/^\/api\/v1\/analysis\/([^/]+)$/);
  if(analysisPath&&method==="POST"){
    const input=await body(req);const workspaceId=typeof input.workspace_id==="string"?input.workspace_id:"";
    if(!await workspaceAccess(auth.user.id,workspaceId,true))return error(req,403,"Workspace write access required",auth.cookie);
    const engineId=ENGINE_PATHS[analysisPath[1]]??(Object.values(ENGINE_PATHS).includes(analysisPath[1])?analysisPath[1]:null);
    if(!engineId)return error(req,404,"Engine not found",auth.cookie);
    const result=analysisResult(engineId,input.demo===true,input.input);await persistAnalysis(auth,workspaceId,result);
    return json(req,result,200,auth.cookie);
  }
  if(path==="/api/v1/monitors"&&method==="GET"){
    const workspaceId=url.searchParams.get("workspace_id");if(!workspaceId||!await workspaceAccess(auth.user.id,workspaceId))return error(req,404,"Workspace not found",auth.cookie);
    return json(req,await bridge("list_monitors",auth.user.id,{workspace_id:workspaceId}),200,auth.cookie);
  }
  if(path==="/api/v1/monitors"&&method==="POST"){
    const input=await body(req);const workspaceId=typeof input.workspace_id==="string"?input.workspace_id:"";if(!await workspaceAccess(auth.user.id,workspaceId,true))return error(req,403,"Workspace write access required",auth.cookie);
    return json(req,await bridge("create_monitor",auth.user.id,{workspace_id:workspaceId,entity:String(input.entity??""),chain:String(input.chain??"ethereum"),rules:input.rules??[],config:input.config??{}}),200,auth.cookie);
  }
  const monitorCheck=path.match(/^\/api\/v1\/monitors\/([^/]+)\/check$/);
  if(monitorCheck&&method==="POST"){
    const monitorId=decodeURIComponent(monitorCheck[1]);const monitor=await bridge("get_monitor",auth.user.id,{monitor_id:monitorId});
    const result=analysisResult("B3",false,{entity:monitor.entity,chain:monitor.chain});await persistAnalysis(auth,monitor.workspace_id,result);
    await bridge("update_monitor_result",auth.user.id,{monitor_id:monitorId,analysis_id:result.analysis_id,status:result.status});
    return json(req,result,200,auth.cookie);
  }
  return error(req,404,"Not found",auth.cookie);
}

Deno.serve(async(req:Request)=>{
  if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors(req)});
  const url=new URL(req.url);
  const marker="/rivexis-api";
  const position=url.pathname.indexOf(marker);
  const path=position>=0?url.pathname.slice(position+marker.length)||"/":url.pathname;
  try{
    if(path==="/health")return json(req,{status:"ready",service:"rivexis-api",runtime:"supabase-edge",api_version:"v1",environment:"production"});
    if(path.startsWith("/api/v1/auth/web/login")||path.startsWith("/api/v1/auth/web/signup")||path.startsWith("/api/v1/auth/email-verification/")||path.startsWith("/api/v1/auth/password-reset/"))return await handleAuth(req,path);
    const auth=await authenticate(req);
    if(!auth)return error(req,401,"Authentication required",clearCookie());
    return await handleApi(req,path,url,auth);
  }catch(cause){
    console.error("rivexis-api request failed",cause instanceof Error?cause.message:JSON.stringify(cause));
    return error(req,500,"Rivexis could not complete the request safely");
  }
});
