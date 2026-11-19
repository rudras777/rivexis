import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import {createClient} from 'npm:@supabase/supabase-js@2.117.3';
import {client} from '../rivexis-api/defi-rpc.mjs';
import {snapshot} from '../rivexis-api/defi-portfolio-rpc.mjs';
import {runMonitorCycle,monitorConfiguration,readBrevoResult} from './cycle.mjs';

const env=(name:string)=>Deno.env.get(name);
const reply=(body:unknown,status=200)=>Response.json(body,{status,headers:{'cache-control':'no-store'}});
function authorized(value:string|null){
  const expected=env('RIVEXIS_DEFI_MONITOR_TOKEN')??'';
  if(expected.length<32||expected.length>256||value?.length!==expected.length)return false;
  let diff=0;for(let i=0;i<expected.length;i++)diff|=expected.charCodeAt(i)^value.charCodeAt(i);return diff===0;
}
Deno.serve(async(req:Request)=>{
  if(req.method!=='POST')return reply({detail:'POST required'},405);
  if(!authorized(req.headers.get('x-rivexis-monitor-token')))return reply({detail:'Scheduled worker authentication required'},401);
  const admin=createClient(env('SUPABASE_URL')!,env('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false,autoRefreshToken:false}});
  const job=async(action:string,payload:Record<string,unknown>={})=>{
    const {data,error}=await admin.rpc('rivexis_defi_monitor_job',{p_action:action,p_payload:payload});
    if(error)throw new Error('Monitoring persistence unavailable');return data;
  };
  const config=monitorConfiguration(env),controller=new AbortController();
  // Bound the entire invocation, including protocol reads and response bodies.
  const timer=setTimeout(()=>controller.abort(),55000);
  const rpc=client(config.url||'https://ethereum.publicnode.com',{signal:controller.signal});
  try{
    const result=await runMonitorCycle({job,enabled:config.enabled,emailEnabled:config.emailEnabled,
      readSnapshot:async(rule:{wallet:string;coverage:string})=>{
        const quota=await admin.rpc('rivexis_defi_quota',{p_wallet:rule.wallet});
        if(quota.error||quota.data!==true)throw new Error('Quota confirmation unavailable');
        return snapshot(rule.wallet,rpc,rule.coverage);
      },
      verifyBlock:async(number:string,hash:string)=>(await rpc.getBlock({blockNumber:BigInt(number)})).hash?.toLowerCase()===hash.toLowerCase(),
      send:async(event:{id:string;recipient:string;kind:string;created_at:string})=>{
        const response=await fetch('https://api.brevo.com/v3/smtp/email',{
          method:'POST',redirect:'error',signal:AbortSignal.any([controller.signal,AbortSignal.timeout(8000)]),
          headers:{'content-type':'application/json','api-key':env('BREVO_API_KEY')!},
          body:JSON.stringify({to:[{email:event.recipient}],templateId:config.templateId,
            params:{eventKind:event.kind==='BREACH'?'Risk threshold reached':'Recovery threshold reached',observedAt:event.created_at,reviewUrl:'https://rivexis.rvea.info/workspace/reports'},
            headers:{idempotencyKey:event.id},tags:['rivexis-defi-risk',`rvx-event:${event.id}`]})
        });
        // Never retain or log raw provider bodies; only the receipt ID is stored.
        return readBrevoResult(response);
      }
    });
    return reply(result);
  }catch{return reply({detail:'Monitoring cycle could not be confirmed. Inspect durable records before retrying.'},503)}
  finally{clearTimeout(timer);controller.abort()}
});
