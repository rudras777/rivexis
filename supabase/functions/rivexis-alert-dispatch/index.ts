import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {createClient} from "npm:@supabase/supabase-js@2.117.3";
import {alertEmail,classifyBrevo,idempotencyUuid,validEmail} from "./delivery.mjs";

type Json=Record<string,unknown>;
type ClaimedAlert={
  id:string;workspace_id:string;workspace_name?:string|null;monitor_id?:string|null;analysis_id?:string|null;
  severity:string;status:string;occurrence_count:number;delivery_attempts:number;claim_token:string;
  payload?:Record<string,unknown>;created_at:string;recipient_email?:string|null;
};

const SUPABASE_URL=Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const BREVO_URL="https://api.brevo.com/v3/smtp/email";
const admin=createClient(SUPABASE_URL,SERVICE_KEY,{auth:{persistSession:false,autoRefreshToken:false}});

function json(body:unknown,status=200){
  return new Response(JSON.stringify(body),{
    status,
    headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"},
  });
}
function intEnv(name:string,fallback:number,min:number,max:number){
  const parsed=Number(Deno.env.get(name)??fallback);
  return Number.isFinite(parsed)?Math.max(min,Math.min(max,Math.trunc(parsed))):fallback;
}
function timeoutEnv(){
  const parsed=Number(Deno.env.get("RIVEXIS_BREVO_TIMEOUT_SECONDS")??8);
  return Number.isFinite(parsed)?Math.max(1,Math.min(30,parsed)):8;
}
function brevoConfig(){
  const apiKey=(Deno.env.get("BREVO_API_KEY")??"").trim();
  const senderEmail=(Deno.env.get("RIVEXIS_BREVO_SENDER_EMAIL")??"").trim();
  const senderName=(Deno.env.get("RIVEXIS_BREVO_SENDER_NAME")??"Rivexis").trim()||"Rivexis";
  const sandbox=(Deno.env.get("RIVEXIS_BREVO_SANDBOX")??"false").trim().toLowerCase()==="true";
  return {
    apiKey,senderEmail,senderName,sandbox,
    ready:Boolean(apiKey&&validEmail(senderEmail)),
    maxAttempts:intEnv("RIVEXIS_ALERT_MAX_ATTEMPTS",5,1,20),
    retryBaseSeconds:intEnv("RIVEXIS_ALERT_RETRY_BASE_SECONDS",30,1,3600),
    batchSize:intEnv("RIVEXIS_ALERT_DISPATCH_BATCH_SIZE",20,1,50),
    timeoutSeconds:timeoutEnv(),
  };
}
async function bridge(action:string,token:string,payload:Json={}):Promise<any>{
  const {data,error}=await admin.rpc("rivexis_edge_alert_dispatch",{p_action:action,p_token:token,p_payload:payload});
  if(error)throw new Error(error.message);
  return data;
}
async function runtime():Promise<Record<string,unknown>|null>{
  const {data,error}=await admin.rpc("rivexis_edge_alert_delivery_runtime");
  if(error)return null;
  return data&&typeof data==="object"?data as Record<string,unknown>:null;
}
async function heartbeat(token:string,payload:Json){
  await bridge("heartbeat",token,payload);
}
async function mark(token:string,alert:ClaimedAlert,success:boolean,errorCode=""){
  return await bridge("mark",token,{
    alert_id:alert.id,
    claim_token:alert.claim_token,
    success,
    error_code:errorCode,
    max_attempts:intEnv("RIVEXIS_ALERT_MAX_ATTEMPTS",5,1,20),
    retry_base_seconds:intEnv("RIVEXIS_ALERT_RETRY_BASE_SECONDS",30,1,3600),
  });
}
async function brevoSend(alert:ClaimedAlert,cfg:ReturnType<typeof brevoConfig>){
  if(!validEmail(alert.recipient_email??""))return {ok:false,error_code:"recipient_email_invalid"};
  const content=alertEmail(alert);
  const idempotencyKey=await idempotencyUuid(alert.id);
  const body={
    sender:{email:cfg.senderEmail,name:cfg.senderName},
    to:[{email:alert.recipient_email,contactPixelTrackingConsent:false}],
    subject:content.subject,
    htmlContent:content.html,
    textContent:content.text,
    headers:{"idempotencyKey":idempotencyKey},
    tags:["rivexis-alert",content.synthetic?"rivexis-synthetic":"rivexis-persisted"],
  };
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(),Math.round(cfg.timeoutSeconds*1000));
  try{
    const response=await fetch(BREVO_URL,{
      method:"POST",
      headers:{"accept":"application/json","content-type":"application/json","api-key":cfg.apiKey},
      body:JSON.stringify(body),
      signal:controller.signal,
    });
    let providerCode="";
    if(response.status===400){
      try{
        const parsed=await response.json();
        if(parsed&&typeof parsed==="object"&&"code" in parsed&&typeof parsed.code==="string")providerCode=parsed.code;
      }catch{/* Provider body is intentionally not reflected or persisted. */}
    }
    return classifyBrevo(response.status,providerCode);
  }catch(cause){
    if(cause instanceof DOMException&&cause.name==="AbortError")return {ok:false,error_code:"brevo_timeout"};
    return {ok:false,error_code:"brevo_transport_error"};
  }finally{
    clearTimeout(timer);
  }
}

async function runDispatch(token:string){
  const cfg=brevoConfig();
  if(!cfg.ready){
    await heartbeat(token,{processor_status:"SCHEDULED_NO_SINK",sink_status:"NOT_CONFIGURED",processed:0,delivered:0,failed:0});
    return {status:"scheduled_no_sink",processed:0,delivered:0,failed:0};
  }
  if(cfg.sandbox){
    await heartbeat(token,{processor_status:"SCHEDULED_SANDBOX",sink_status:"BREVO_SANDBOX",processed:0,delivered:0,failed:0});
    return {status:"scheduled_sandbox",processed:0,delivered:0,failed:0};
  }

  const claimed=await bridge("claim",token,{limit:cfg.batchSize});
  const items=Array.isArray(claimed?.items)?claimed.items as ClaimedAlert[]:[];
  let delivered=0;
  let failed=0;
  let firstError="";
  for(const alert of items){
    const outcome=await brevoSend(alert,cfg);
    if(outcome.ok){
      try{
        await mark(token,alert,true);
        delivered+=1;
      }catch{
        failed+=1;
        firstError ||= "delivery_mark_failed";
      }
    }else{
      const code=typeof outcome.error_code==="string"?outcome.error_code:"delivery_error";
      try{await mark(token,alert,false,code)}catch{/* Lease expiry safely makes the row retryable. */}
      failed+=1;
      firstError ||= code;
    }
  }
  await heartbeat(token,{
    processor_status:failed?"DEGRADED":"SCHEDULED_READY",
    sink_status:"BREVO_READY",
    error_code:firstError,
    processed:items.length,
    delivered,
    failed,
  });
  console.log(JSON.stringify({event:"rivexis_alert_dispatch_cycle",processed:items.length,delivered,failed,processor_status:failed?"DEGRADED":"SCHEDULED_READY"}));
  return {status:failed?"degraded":"ready",processed:items.length,delivered,failed};
}

Deno.serve(async(req:Request)=>{
  const url=new URL(req.url);
  if(req.method==="GET"&&url.pathname.endsWith("/health")){
    const cfg=brevoConfig();
    const state=await runtime();
    return json({
      status:"ready",
      service:"rivexis-alert-dispatch",
      runtime:"supabase-edge",
      api_version:"v1",
      scheduler:"supabase-cron",
      processor_status:state?.processor_status??"BOOTSTRAP",
      sink_status:state?.sink_status??(cfg.ready?(cfg.sandbox?"BREVO_SANDBOX":"BREVO_READY"):"NOT_CONFIGURED"),
      recipient_policy:"WORKSPACE_OWNER_EMAIL",
      continuous_threat_ingestion:false,
    });
  }
  if(req.method!=="POST")return json({detail:"Not found"},404);
  const token=(req.headers.get("x-rivexis-dispatch-token")??"").trim();
  if(!token)return json({detail:"Dispatch authentication required"},401);
  try{
    const result=await runDispatch(token);
    return json(result);
  }catch(cause){
    const detail=cause instanceof Error?cause.message.toLowerCase():"";
    if(detail.includes("dispatch authorization failed"))return json({detail:"Dispatch authentication failed"},401);
    console.error(JSON.stringify({event:"rivexis_alert_dispatch_error",error_type:cause instanceof Error?cause.name:"Error"}));
    return json({detail:"Alert dispatch failed safely"},500);
  }
});
