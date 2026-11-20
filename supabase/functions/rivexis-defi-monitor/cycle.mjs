import {evaluateMonitor,deliveryOutcome} from '../rivexis-api/defi-monitor-policy.mjs';

export async function runMonitorCycle({job,reserve=async(/** @type {{wallet:string}} */ _rule)=>false,readSnapshot,verifyBlock,send,enabled=false,emailEnabled=false,now=()=>Date.now()}) {
  // Cron is the durable scheduler. An invocation performs at most one evaluation
  // and one outbox attempt. No interval, waitUntil or background promise.
  await job('heartbeat',{evaluation_enabled:enabled,email_enabled:enabled&&emailEnabled});
  if(!enabled)return {state:'INACTIVE',evaluated:0,attempted:0};
  const rule=await job('claim');
  let evaluated=0;
  if(rule){
    const identity={id:rule.id,version:rule.version,lease_token:rule.lease_token};
    try{
      // The shared gate covers revalidation as well as the new snapshot. An
      // unavailable/denied acknowledgement must prevent every provider read.
      if(await reserve(rule)!==true)throw new Error('Quota confirmation unavailable');
      // Invalidate previously accepted evidence after a detected reorganization.
      if(rule.block_number&&rule.block_hash&&!await verifyBlock(rule.block_number,rule.block_hash)){
        await job('reorg',identity);
      }else{
        const result=evaluateMonitor(rule,await readSnapshot(rule),now());
        if(rule.block_number&&BigInt(result.block_number)<BigInt(rule.block_number))throw new Error('Older block');
        const committed=await job('complete',{...identity,result});
        if(committed?.committed)evaluated=1;
      }
    }catch{
      // If commit acknowledgement was lost, the old lease cannot overwrite a
      // completed evaluation. Never repeat a logical write or inference.
      await job('unavailable',identity);
    }
  }
  if(!emailEnabled)return {state:'SCHEDULED',evaluated,attempted:0};
  const event=await job('claim_delivery');
  if(!event)return {state:'SCHEDULED',evaluated,attempted:0};
  let outcome;
  try{const response=await send(event);outcome=deliveryOutcome(response.status,response.body)}
  catch{outcome={state:'UNKNOWN',error_code:'ACCEPTANCE_UNCONFIRMED'}}
  // A lost acknowledgement leaves SENDING; database restart recovery changes
  // it to UNKNOWN, never QUEUED. Only confirmed 429 rejections can retry.
  await job('mark_delivery',{id:event.id,delivery_token:event.delivery_token,...outcome});
  return {state:'SCHEDULED',evaluated,attempted:1};
}

export function monitorConfiguration(env) {
  const url=env('ETHEREUM_RPC_URL')??'';
  let allowed=false;
  try{const u=new URL(url);allowed=u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&['eth-mainnet.g.alchemy.com','ethereum.publicnode.com'].includes(u.hostname)}catch{}
  const enabled=env('RIVEXIS_DEFI_MONITOR_ENABLED')==='true'&&env('RIVEXIS_MONITOR_RPC_APPROVED')==='true'&&allowed;
  const template=env('RIVEXIS_BREVO_DEFI_TEMPLATE_ID')??'';
  return {enabled,url,templateId:/^[1-9]\d{0,8}$/.test(template)?Number(template):null,
    emailEnabled:enabled&&env('RIVEXIS_DEFI_MONITOR_EMAIL_ENABLED')==='true'&&!!env('BREVO_API_KEY')&&/^[1-9]\d{0,8}$/.test(template)};
}

export async function readBrevoResult(response) {
  const reader=response.body?.getReader();
  if(!reader)return {status:response.status,body:null};
  let bytes=0,text='';const decoder=new TextDecoder();
  try{
    for(;;){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>16384){await reader.cancel();return {status:response.status,body:null}}text+=decoder.decode(value,{stream:true})}
    text+=decoder.decode();let body=null;try{body=JSON.parse(text)}catch{}
    return {status:response.status,body};
  }finally{reader.releaseLock()}
}
