import {monitorInput} from './defi-monitor-policy.mjs';
import {readRequestText} from './defi-http.mjs';

export async function handleDefiMonitor(req,owner,admin,enabled=false) {
  const reply=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json','cache-control':'no-store'}});
  if(!owner)return reply({detail:'Authentication required'},401);
  if(!['GET','PATCH'].includes(req.method))return reply({detail:'GET or PATCH required'},405);
  if(!enabled)return req.method==='GET'?reply({runtime:{state:'INACTIVE',email:false,interval_minutes:30},rule:null,events:[]}):reply({detail:'Scheduled risk monitoring is not activated. No settings were changed.'},503);
  let payload={};
  if(req.method==='PATCH'){
    try{payload=monitorInput(JSON.parse(await readRequestText(req)))}catch{return reply({detail:'Invalid monitoring settings. Use supported coverage, explicit preferences and valid thresholds.'},422)}
  }
  try{
    const result=await admin.rpc('rivexis_defi_monitor_manage',{p_owner:owner,p_action:req.method==='GET'?'read':'save',p_payload:payload});
    if(result.error?.code==='P0001'&&['Bounded monitoring capacity reached','Monitoring runtime is inactive'].includes(result.error.message))return reply({detail:result.error.message},409);
    if(result.error||!result.data||typeof result.data!=='object'||!result.data.runtime)return reply({detail:req.method==='GET'?'Monitoring records unavailable':'Save could not be confirmed. Reload monitoring settings before retrying.'},503);
    if((result.data.rule&&result.data.rule.owner_id!==owner)||(req.method==='PATCH'&&!result.data.rule))return reply({detail:'Monitoring ownership or save confirmation is unavailable. Reload records before retrying.'},503);
    return reply(result.data);
  }catch{return reply({detail:req.method==='GET'?'Monitoring records unavailable':'Save could not be confirmed. Reload monitoring settings before retrying.'},503)}
}
