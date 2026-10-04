"use client";

import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type AlertRow={
  id:string;workspace_id:string;monitor_id?:string|null;analysis_id?:string|null;severity:string;status:string;
  provider_id?:string|null;occurrence_count:number;delivery_status:string;delivery_attempts:number;next_delivery_at?:string|null;
  last_delivery_error?:string|null;delivered_at?:string|null;dead_lettered_at?:string|null;created_at:string;updated_at:string;
  payload?:Record<string,unknown>;
};
type AlertList={workspace_id:string;items:AlertRow[];status:string};
type Metrics={
  workspace_id:string;window_hours:number;slo_seconds:number;total:number;pending:number;delivered:number;dead_letter:number;
  oldest_pending_age_seconds:number;delivered_within_slo_percent:number|null;processor_status:string;sink_status?:string;
  recipient_policy?:string;last_run_at?:string|null;last_success_at?:string|null;last_error_code?:string|null;
  last_processed?:number;last_delivered?:number;last_failed?:number;
};

type StatusVars={workspaceId:string;id:string;status:"open"|"acknowledged"|"resolved"};
type RequeueVars={workspaceId:string;id:string};

function message(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load alert records.";
    if(error.status===403)return "Your workspace role does not permit this alert operation.";
    if(error.status===404)return "This alert or workspace is no longer available to your account.";
    if(error.status===422)return "Rivexis rejected the requested alert state.";
    if(error.status===503)return "Alert services are temporarily unavailable.";
  }
  return "Rivexis could not complete the alert operation.";
}
function recordedAt(value:string){const date=new Date(value);return Number.isNaN(date.getTime())?value:date.toLocaleString()}
function age(seconds:number){if(seconds<60)return `${Math.round(seconds)}s`;if(seconds<3600)return `${Math.round(seconds/60)}m`;return `${Math.round(seconds/3600)}h`}
function severityClass(value:string){const v=value.toLowerCase();return v==="critical"||v==="high"?"negative":v==="moderate"?"warning":v==="low"?"positive":"neutral"}
function processorTruth(metrics?:Metrics){
  const status=String(metrics?.processor_status??"NOT_CONFIGURED").toUpperCase();
  const sink=String(metrics?.sink_status??"NOT_CONFIGURED").toUpperCase();
  if(status==="SCHEDULED_READY")return "Automatic queue scheduling is active. Brevo submissions are enabled for the workspace-owner recipient policy. A delivered queue state means provider acceptance, not proof of inbox delivery. Continuous threat ingestion is still not configured.";
  if(status==="SCHEDULED_SANDBOX")return "Automatic queue scheduling is active in Brevo sandbox mode. No notification email is sent and queued records are not consumed. Continuous threat ingestion is still not configured.";
  if(status==="SCHEDULED_NO_SINK"||sink==="NOT_CONFIGURED")return "Automatic queue scheduling is active, but no production alert-delivery sink is configured. Queued records remain pending without consuming delivery attempts. Continuous threat ingestion is still not configured.";
  if(status==="DEGRADED")return "Automatic queue scheduling is active but the last delivery cycle reported a degraded outcome. Queue retry and dead-letter controls remain authoritative; continuous threat ingestion is still not configured.";
  return "This compatibility runtime exposes durable alert records and queue state. Continuous threat ingestion and automatic delivery processing are not configured.";
}
function recipientLabel(value?:string){return value==="WORKSPACE_OWNER_EMAIL"?"Workspace owner email":"Not configured"}

export default function Alerts(){
  const {workspaceId,workspace}=useWorkspace();
  const qc=useQueryClient();
  const list=useQuery({queryKey:workspaceQueryKey(workspaceId,"alerts"),queryFn:()=>api<AlertList>(`/api/v1/alerts?workspace_id=${encodeURIComponent(workspaceId)}`),retry:false});
  const metrics=useQuery({queryKey:workspaceQueryKey(workspaceId,"alert-metrics"),queryFn:()=>api<Metrics>(`/api/v1/alerts/delivery-metrics?workspace_id=${encodeURIComponent(workspaceId)}&slo_seconds=300`),retry:false});
  const statusMutation=useMutation({
    mutationFn:(vars:StatusVars)=>api<AlertRow>(`/api/v1/alerts/${encodeURIComponent(vars.id)}?status=${encodeURIComponent(vars.status)}`,{method:"PATCH"}),
    onSuccess:(_row,vars)=>{void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"alerts")});void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"alert-metrics")});},
  });
  const requeue=useMutation({
    mutationFn:(vars:RequeueVars)=>api<AlertRow>(`/api/v1/alerts/${encodeURIComponent(vars.id)}/requeue`,{method:"POST"}),
    onSuccess:(_row,vars)=>{void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"alerts")});void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"alert-metrics")});},
  });
  const alerts=list.data?.items??[];
  const open=alerts.filter(item=>item.status==="open").length;
  const acknowledged=alerts.filter(item=>item.status==="acknowledged").length;
  const busy=statusMutation.isPending||requeue.isPending;
  const runtime=metrics.data;
  return <>
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">Operational evidence queue</div><h1>Alerts</h1><p>Review durable workspace alert records and delivery state without implying continuous provider surveillance.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name}</span><span className="badge">DURABLE RECORDS</span></div></div>
    <section className="overviewBand surfaceOverview" aria-label="Alert overview"><div><small>TOTAL / 24H</small><strong>{metrics.isPending?"—":runtime?.total??0}</strong><span>Recorded alerts</span></div><div><small>OPEN</small><strong>{list.isPending?"—":open}</strong><span>Awaiting review</span></div><div><small>ACKNOWLEDGED</small><strong>{list.isPending?"—":acknowledged}</strong><span>Under review</span></div><div><small>DELIVERY QUEUE</small><strong>{metrics.isPending?"—":runtime?.pending??0}</strong><span>Pending or retry</span></div></section>
    <div className="truthNotice" data-testid="alert-runtime-truth"><span className="statusDot"/>{processorTruth(runtime)}</div>
    {runtime?<section className="panel operationalPanel"><div className="panelHeading"><div><span className="workspaceKicker">24-hour delivery posture</span><h2>Queue controls</h2></div><span className="stepLabel">PROCESSOR {runtime.processor_status}</span></div><div className="resultGrid"><div><span>Provider accepted</span><b>{runtime.delivered}</b></div><div><span>Dead letter</span><b>{runtime.dead_letter}</b></div><div><span>Oldest queued</span><b>{age(runtime.oldest_pending_age_seconds)}</b></div><div><span>Accepted within 5m</span><b>{runtime.delivered_within_slo_percent==null?"No accepted submissions":`${runtime.delivered_within_slo_percent}%`}</b></div><div><span>Delivery sink</span><b>{runtime.sink_status??"NOT_CONFIGURED"}</b></div><div><span>Recipient policy</span><b>{recipientLabel(runtime.recipient_policy)}</b></div><div><span>Last processor run</span><b>{runtime.last_run_at?recordedAt(runtime.last_run_at):"No run recorded"}</b></div><div><span>Last cycle</span><b>{`${runtime.last_delivered??0} accepted / ${runtime.last_failed??0} failed`}</b></div></div><p className="sectionLead">Requeue resets a dead-letter record to pending. Provider acceptance is tracked separately from threat evidence and does not prove inbox delivery.</p></section>:null}
    <section className="panel operationalPanel" aria-live="polite" data-testid="workspace-alerts-state"><div className="panelHeading"><div><span className="workspaceKicker">Authorized inventory</span><h2>Alert records</h2></div><p className="sectionLead">Rows are workspace-authorized on the server. Status changes require write access; requeue requires OWNER/ADMIN management access.</p></div>
      {list.isPending?<div className="surfaceState" role="status">Loading alerts for {workspace.name}…</div>:null}
      {list.isError?<p className="error" role="alert">{message(list.error)}</p>:null}
      {!list.isPending&&!list.isError&&!alerts.length?<div className="surfaceState"><b>No durable alerts are recorded in this workspace.</b><span>This is not evidence that no threats exist. The current compatibility runtime has no continuous provider threat stream.</span></div>:null}
      {!list.isPending&&!list.isError&&alerts.length?<div className="tableWrap"><table className="table"><thead><tr><th>Severity</th><th>State</th><th>Reference</th><th>Delivery</th><th>Recorded</th><th>Actions</th></tr></thead><tbody>{alerts.map(item=><tr key={item.id}><td><span className={`statePill ${severityClass(item.severity)}`}>{item.severity}</span></td><td><span className="statePill neutral">{item.status}</span></td><td><code>{item.id}</code>{item.analysis_id?<small style={{display:"block"}}>Analysis {item.analysis_id}</small>:null}</td><td><span className="statePill neutral">{item.delivery_status}</span><small style={{display:"block"}}>Attempts {item.delivery_attempts}</small></td><td>{recordedAt(item.created_at)}</td><td><div className="actions"><button className="ghost compactButton" disabled={busy||item.status==="acknowledged"} onClick={()=>statusMutation.mutate({workspaceId,id:item.id,status:"acknowledged"})}>Acknowledge</button><button className="ghost compactButton" disabled={busy||item.status==="resolved"} onClick={()=>statusMutation.mutate({workspaceId,id:item.id,status:"resolved"})}>Resolve</button>{item.delivery_status==="dead_letter"?<button className="button compactButton" disabled={busy} onClick={()=>requeue.mutate({workspaceId,id:item.id})}>Requeue</button>:null}</div></td></tr>)}</tbody></table></div>:null}
      {statusMutation.isError?<p className="error" role="alert">{message(statusMutation.error)}</p>:null}
      {requeue.isError?<p className="error" role="alert">{message(requeue.error)}</p>:null}
    </section>
  </>;
}