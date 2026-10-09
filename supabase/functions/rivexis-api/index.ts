import {brandedPdf as minimalPdf} from "./report-pdf.mjs";
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient, type SupabaseClient, type User} from "npm:@supabase/supabase-js@2.117.3";
import {analysisResult} from "./analysis.mjs";
import {createMembershipClaimToken,hashMembershipClaimToken} from "./membership.mjs";
import {parseRole,roleOrDefault} from "./role.mjs";
import {handleDefi,validWallet,readRequestText} from "./defi-http.mjs";
import {client} from "./defi-rpc.mjs";
import {snapshot,COVERAGE} from "./defi-portfolio-rpc.mjs";
import {frontier} from "./defi-unified-model.mjs";
import {sampleSnapshot} from "./defi-sample.mjs";

type Json=Record<string,unknown>;
type SessionCookie={access_token:string;refresh_token:string;csrf:string};
type AuthContext={user:User;appUser:Json;session:SessionCookie;cookie?:string};

const SUPABASE_URL=Deno.env.get("SUPABASE_URL")!;
const ANON_KEY=Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_KEY=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const LIVE_ORIGIN="https://rivexis-web.rudrasingh0718.workers.dev";
const COOKIE="rvx_session";
const ORG_ROLES=new Set(["OWNER","ADMIN","ANALYST","VIEWER"]);
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

async function organizationWorkspaceBridge(userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_create_organization_workspace",{p_actor_user_id:userId,p_payload:payload});
  if(error)throw new Error(error.message);
  return data;
}

async function savedBridge(action:string,userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_saved_analysis",{p_action:action,p_actor_user_id:userId,p_payload:payload});
  if(error)throw new Error(error.message);
  return data;
}

async function membershipBridge(action:string,userId:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_organization_membership",{p_action:action,p_actor_user_id:userId,p_payload:payload});
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
  return new Response(new Uint8Array(body).buffer,{status:200,headers});
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
async function body(req:Request):Promise<Json>{
  try{const value=await req.json();return value&&typeof value==="object"&&!Array.isArray(value)?value as Json:{}}catch{return {}}
}

async function ensureAppUser(user:User){
  return await bridge("ensure_user",user.id,{email:(user.email??"").toLowerCase(),role:roleOrDefault(user.user_metadata?.role)}) as Json;
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

function membershipFailure(req:Request,cause:unknown,cookie?:string){
  const detail=cause instanceof Error?cause.message:"Organization membership request failed";
  const normalized=detail.toLowerCase();
  if(normalized.includes("organization administration required")||normalized.includes("only an organization owner"))return error(req,403,detail,cookie);
  if(normalized.includes("organization not found")||normalized.includes("user must already have a rivexis account"))return error(req,404,detail,cookie);
  if(normalized.includes("invalid organization role"))return error(req,422,detail,cookie);
  if(normalized.includes("membership claim")||normalized.includes("last organization owner")||normalized.includes("new organization members require"))return error(req,409,detail,cookie);
  return error(req,500,"Rivexis could not complete the membership request safely",cookie);
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
  const row=rows.find((item:Json)=>item.id===workspaceId)??null;
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
    const userRole=parseRole(input.role);
    if(!email||password.length<8||!userRole)return error(req,422,"Check your email, password, and role, then try again");
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


async function persistAnalysis(auth:AuthContext,workspaceId:string,result:Json){
  await bridge("create_analysis",auth.user.id,{workspace_id:workspaceId,analysis_id:result.analysis_id,engine_id:result.engine_id,demo:result.demo,status:result.status,result});
}

async function handleApi(req:Request,path:string,url:URL,auth:AuthContext){
  const method=req.method.toUpperCase();
  const write=["POST","PUT","PATCH","DELETE"].includes(method);
  if(write&&!requireCsrf(req,auth))return error(req,403,"CSRF validation failed",auth.cookie);
  if((path.startsWith("/api/v1/defi/")||path==="/api/v1/defi-reports")&&!auth.user.email_confirmed_at)return error(req,403,"Email verification is required before analysis or reports",auth.cookie);
  if(path.startsWith("/api/v1/defi/")){
    const result=await handleDefi(req,path,admin,Deno.env.get("ETHEREUM_RPC_URL")||"https://ethereum.publicnode.com");
    if(auth.cookie)result.headers.set("set-cookie",auth.cookie);
    return result;
  }

  if(path==="/api/v1/defi-reports"&&method==="GET"){
    const result=await admin.from("rivexis_defi_reports").select("id,created_at,receipt").eq("owner_id",auth.user.id).order("created_at",{ascending:false}).limit(20);
    if(result.error)return error(req,503,"Reports are temporarily unavailable",auth.cookie);
    return json(req,{items:result.data},200,auth.cookie);
  }
  if(path==="/api/v1/defi-reports"&&method==="POST"){
    if(Number(req.headers.get("content-length")||0)>8192)return error(req,413,"Report request too large",auth.cookie);
    let raw:string;try{raw=await readRequestText(req,8192)}catch(cause){return error(req,cause instanceof Error&&cause.message==="Request is too large"?413:422,"Invalid or oversized report request",auth.cookie)};
    let input:Json;try{input=JSON.parse(raw)}catch{return error(req,422,"Invalid report request",auth.cookie)};
    if(!input||typeof input!=="object"||Array.isArray(input))return error(req,422,"Invalid report request",auth.cookie);
    if(typeof input.budget!=="string"||typeof input.target!=="string"||typeof input.gasReserve!=="string"||typeof input.objective!=="string"||!input.shocks||typeof input.shocks!=="object"||Array.isArray(input.shocks))return error(req,422,"Invalid report constraints",auth.cookie);
    if(input.sample!==true){
      if(input.coverage!==undefined&&(typeof input.coverage!=="string"||!COVERAGE.includes(input.coverage)))return error(req,422,"Unsupported coverage",auth.cookie);
      if(typeof input.wallet!=="string"||!validWallet(input.wallet))return error(req,422,"Invalid wallet",auth.cookie);
      const quota=await admin.rpc("rivexis_defi_quota",{p_wallet:input.wallet.toLowerCase()});
      if(quota.error)return error(req,503,"Quota service unavailable",auth.cookie);
      if(quota.data!==true)return error(req,429,"Free beta quota reached",auth.cookie);
    }
    try{
      const state=input.sample===true?sampleSnapshot():await snapshot(input.wallet,client(Deno.env.get("ETHEREUM_RPC_URL")||"https://ethereum.publicnode.com"),typeof input.coverage==='string'?input.coverage:'aave');
      const constraints={budget:input.budget,target:input.target,gasReserve:input.gasReserve,shocks:input.shocks,objective:input.objective};
      const result=frontier(state,constraints);
      const receipt={model:result.model,sample:input.sample===true,snapshot:state,constraints,result,createdAt:now(),classification:"MODEL_COMPARISON_NOT_EXECUTION"};
      const saved=await admin.rpc("rivexis_defi_save_report",{p_owner:auth.user.id,p_receipt:receipt});
      if(saved.error)return error(req,409,"Report could not be saved. Accounts are limited to 20 reports.",auth.cookie);
      return json(req,{id:saved.data,receipt},201,auth.cookie);
    }catch{return error(req,422,"Report requires valid constraints and fresh supported protocol evidence",auth.cookie);}
  }

  if(path==="/api/v1/auth/web/csrf")return json(req,{csrf_token:auth.session.csrf},200,auth.cookie);
  if(path==="/api/v1/auth/logout"&&method==="POST"){
    const client=createClient(SUPABASE_URL,ANON_KEY,{auth:{persistSession:false,autoRefreshToken:false}});
    await client.auth.setSession({access_token:auth.session.access_token,refresh_token:auth.session.refresh_token});
    await client.auth.signOut({scope:"local"});
    return json(req,{status:"revoked",scope:"current_session"},200,clearCookie());
  }
  if(path==="/api/v1/me"&&method==="GET")return json(req,{id:auth.user.id,email:auth.user.email,role:auth.appUser.role,email_verified:Boolean(auth.user.email_confirmed_at)},200,auth.cookie);
  if(path==="/api/v1/me/role"&&method==="PATCH"){
    const input=await body(req);const nextRole=parseRole(input.role);
    if(!nextRole)return error(req,422,"Invalid role",auth.cookie);
    return json(req,await bridge("update_role",auth.user.id,{role:nextRole}),200,auth.cookie);
  }
  if(path==="/api/v1/workspaces"&&method==="GET")return json(req,{items:await allWorkspaces(auth.user.id)},200,auth.cookie);
  if(path==="/api/v1/workspaces"&&method==="POST"){
    const input=await body(req);const name=typeof input.name==="string"?input.name.trim():"";const workspaceRole=parseRole(input.role);
    const organizationId=typeof input.organization_id==="string"?input.organization_id.trim():"";
    if(name.length<2||!workspaceRole)return error(req,422,"Workspace name and valid role are required",auth.cookie);
    if(organizationId&&organizationId.length!==36)return error(req,422,"Organization ID is invalid",auth.cookie);
    try{
      const created=organizationId
        ?await organizationWorkspaceBridge(auth.user.id,{name,role:workspaceRole,organization_id:organizationId})
        :await bridge("create_workspace",auth.user.id,{name,role:workspaceRole});
      return json(req,created,200,auth.cookie);
    }catch(cause){
      const detail=cause instanceof Error?cause.message:"Workspace creation failed";
      const normalized=detail.toLowerCase();
      if(normalized.includes("organization write access required")||normalized.includes("organization not found or access denied"))return error(req,403,"Organization write access required",auth.cookie);
      if(normalized.includes("workspace name")||normalized.includes("invalid role")||normalized.includes("organization is required"))return error(req,422,"Workspace name, role, or organization is invalid",auth.cookie);
      return error(req,500,"Rivexis could not create the workspace safely",auth.cookie);
    }
  }
  if(path==="/api/v1/organizations"&&method==="GET"){
    return json(req,await bridge("list_organizations",auth.user.id),200,auth.cookie);
  }
  if(path==="/api/v1/organizations"&&method==="POST"){
    const input=await body(req);const name=typeof input.name==="string"?input.name.trim():"";if(name.length<2)return error(req,422,"Organization name is required",auth.cookie);
    return json(req,await bridge("create_organization",auth.user.id,{name}),200,auth.cookie);
  }
  const membershipClaimCreate=path.match(/^\/api\/v1\/organizations\/([^/]+)\/membership-claim$/);
  if(membershipClaimCreate&&method==="POST"){
    const organizationId=decodeURIComponent(membershipClaimCreate[1]);
    try{
      const claimToken=createMembershipClaimToken();
      const tokenHash=await hashMembershipClaimToken(claimToken);
      const created=await membershipBridge("create_claim",auth.user.id,{organization_id:organizationId,token_hash:tokenHash});
      return json(req,{organization_id:organizationId,claim_token:claimToken,expires_in_seconds:created.expires_in_seconds??900,expires_at:created.expires_at},200,auth.cookie);
    }catch(cause){return membershipFailure(req,cause,auth.cookie)}
  }
  const memberClaimAccept=path.match(/^\/api\/v1\/organizations\/([^/]+)\/members\/claim$/);
  if(memberClaimAccept&&method==="POST"){
    const organizationId=decodeURIComponent(memberClaimAccept[1]);
    const input=await body(req);
    const claimToken=typeof input.claim_token==="string"?input.claim_token.trim():"";
    const nextRole=typeof input.role==="string"?input.role.trim().toUpperCase():"";
    if(!ORG_ROLES.has(nextRole))return error(req,422,"Invalid organization role",auth.cookie);
    try{
      const tokenHash=await hashMembershipClaimToken(claimToken);
      return json(req,await membershipBridge("accept_claim",auth.user.id,{organization_id:organizationId,token_hash:tokenHash,role:nextRole}),200,auth.cookie);
    }catch(cause){return membershipFailure(req,cause,auth.cookie)}
  }
  const membersCollection=path.match(/^\/api\/v1\/organizations\/([^/]+)\/members$/);
  if(membersCollection&&method==="GET"){
    const organizationId=decodeURIComponent(membersCollection[1]);
    try{return json(req,await membershipBridge("list",auth.user.id,{organization_id:organizationId}),200,auth.cookie)}catch(cause){return membershipFailure(req,cause,auth.cookie)}
  }
  if(membersCollection&&method==="POST"){
    const organizationId=decodeURIComponent(membersCollection[1]);
    const input=await body(req);
    const email=typeof input.email==="string"?input.email.trim().toLowerCase():"";
    const nextRole=typeof input.role==="string"?input.role.trim().toUpperCase():"";
    if(!email||!ORG_ROLES.has(nextRole))return error(req,422,"Email and valid organization role are required",auth.cookie);
    try{return json(req,await membershipBridge("update_existing",auth.user.id,{organization_id:organizationId,email,role:nextRole}),200,auth.cookie)}catch(cause){return membershipFailure(req,cause,auth.cookie)}
  }
  const memberDelete=path.match(/^\/api\/v1\/organizations\/([^/]+)\/members\/([^/]+)$/);
  if(memberDelete&&method==="DELETE"){
    const organizationId=decodeURIComponent(memberDelete[1]);
    const targetUserId=decodeURIComponent(memberDelete[2]);
    try{
      const outcome=await membershipBridge("delete",auth.user.id,{organization_id:organizationId,user_id:targetUserId});
      if(outcome?.deleted!==true)return error(req,404,"Organization member not found",auth.cookie);
      return empty(req,204,auth.cookie);
    }catch(cause){return membershipFailure(req,cause,auth.cookie)}
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
    if(path==="/health")return json(req,{status:"ready",service:"rivexis-api",runtime:"supabase-edge",api_version:"v1",environment:"production",capabilities:{organization_workspace_create:true}});
    if(path==="/api/v1/auth/session-status"){
      if(req.method!=="GET")return error(req,405,"GET required");
      const session=await authenticate(req);
      return json(req,{authenticated:Boolean(session),email_verified:Boolean(session?.user.email_confirmed_at)},200,session?session.cookie:(cookieValue(req,COOKIE)?clearCookie():undefined));
    }
    if(path.startsWith("/api/v1/auth/web/login")||path.startsWith("/api/v1/auth/web/signup")||path.startsWith("/api/v1/auth/email-verification/")||path.startsWith("/api/v1/auth/password-reset/"))return await handleAuth(req,path);
    const auth=await authenticate(req);
    if(!auth)return error(req,401,"Authentication required",clearCookie());
    return await handleApi(req,path,url,auth);
  }catch(cause){
    console.error("rivexis-api request failed",cause instanceof Error?cause.message:JSON.stringify(cause));
    return error(req,500,"Rivexis could not complete the request safely");
  }
});
