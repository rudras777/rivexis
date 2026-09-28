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
type Metrics={workspace_id:string;window_hours:number;slo_seconds:number;total:number;pending:number;delivered:number;dead_letter:number;oldest_pending_age_seconds:number;delivered_within_slo_percent:number|null;processor_status:string};

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
  return <>
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">Operational evidence queue</div><h1>Alerts</h1><p>Review durable workspace alert records and delivery state without implying continuous provider surveillance.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name}</span><span className="badge">DURABLE RECORDS</span></div></div>
    <section className="overviewBand surfaceOverview" aria-label="Alert overview"><div><small>TOTAL / 24H</small><strong>{metrics.isPending?"—":metrics.data?.total??0}</strong><span>Recorded alerts</span></div><div><small>OPEN</small><strong>{list.isPending?"—":open}</strong><span>Awaiting review</span></div><div><small>ACKNOWLEDGED</small><strong>{list.isPending?"—":acknowledged}</strong><span>Under review</span></div><div><small>DELIVERY QUEUE</small><strong>{metrics.isPending?"—":metrics.data?.pending??0}</strong><span>Pending or retry</span></div></section>
    <div className="truthNotice"><span className="statusDot"/>This compatibility runtime exposes durable alert records and queue state only. Continuous threat ingestion and automatic delivery processing are not configured.</div>
    {metrics.data?<section className="panel operationalPanel"><div className="panelHeading"><div><span className="workspaceKicker">24-hour delivery posture</span><h2>Queue controls</h2></div><span className="stepLabel">PROCESSOR {metrics.data.processor_status}</span></div><div className="resultGrid"><div><span>Delivered</span><b>{metrics.data.delivered}</b></div><div><span>Dead letter</span><b>{metrics.data.dead_letter}</b></div><div><span>Oldest queued</span><b>{age(metrics.data.oldest_pending_age_seconds)}</b></div><div><span>Within 5m SLO</span><b>{metrics.data.delivered_within_slo_percent==null?"No deliveries":`${metrics.data.delivered_within_slo_percent}%`}</b></div></div><p className="sectionLead">Requeue resets a dead-letter record to pending. It does not claim delivery will occur until a real processor is configured.</p></section>:null}
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
