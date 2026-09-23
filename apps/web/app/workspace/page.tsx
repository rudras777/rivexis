"use client";

import Link from "next/link";
import {useQuery} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

const engines=[['B1','Transaction Simulation'],['B2','Transaction & Contract Security'],['B3','Threat & Monitoring'],['B4','Entity & Fund Flow'],['B5','Cross-Chain Route'],['F1','Portfolio & Exposure'],['F2','Protocol Risk'],['F3','Position & Liquidation'],['F4','Yield & Strategy'],['F5','Treasury & Scenarios']];

type ActivityItem={
  type:"analysis"|"decision"|string;
  id:string;
  engine_id?:string|null;
  demo?:boolean|null;
  created_at:string;
};

function activityError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load workspace activity.";
    if(error.status===403||error.status===404)return "Workspace activity is unavailable because access could not be confirmed.";
    if(error.status===503)return "Workspace activity is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load activity for this workspace.";
}

function recordedAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}

export default function Workspace(){
  const {workspaceId,workspace}=useWorkspace();
  const activity=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"dashboard-activity"),
    queryFn:()=>api<{items:ActivityItem[]}>(`/api/v1/history?limit=6&workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const items=activity.data?.items??[];

  return <>
    <div className="workspaceHeader"><div><h1>Rivexis Workspace</h1><p>Evidence → specialist engines → decision policy → explanation.</p></div><span className="badge">{workspace.name} · {workspace.access_role}</span></div>
    <section className="panel" style={{marginTop:0}}>
      <h2>Product metadata</h2>
      <p className="sectionLead">These values describe the Rivexis product surface. They are not live activity totals for {workspace.name}.</p>
      <div className="metricGrid" style={{marginTop:16}}><div className="metricCard"><small>Core engines</small><strong>10</strong></div><div className="metricCard"><small>Primary domains</small><strong>2</strong></div><div className="metricCard"><small>Decision states</small><strong>5</strong></div><div className="metricCard"><small>Provider-grounded paths</small><strong>10*</strong></div></div>
    </section>
    <section className="panel" aria-live="polite" data-testid="workspace-dashboard-activity">
      <h2>Recent workspace activity · {workspace.name}</h2>
      <p className="sectionLead">This list is loaded from the authorized history API for the active workspace only. It shows up to six recent analysis or decision records.</p>
      {activity.isPending?<p>Loading recent workspace activity…</p>:null}
      {activity.isError?<p className="error" role="alert">{activityError(activity.error)}</p>:null}
      {!activity.isPending&&!activity.isError&&!items.length?<p>No analysis or decision activity is recorded in this workspace yet.</p>:null}
      {!activity.isPending&&!activity.isError&&items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Type</th><th>Engine</th><th>Mode</th><th>Recorded</th></tr></thead><tbody>{items.map(item=><tr key={`${item.type}-${item.id}`}><td>{item.type}</td><td>{item.engine_id??"—"}</td><td>{item.type==="analysis"?(item.demo?"Demo":"Connected/direct"):"—"}</td><td>{recordedAt(item.created_at)}</td></tr>)}</tbody></table></div>:null}
      <div style={{marginTop:14}}><Link className="ghost" href="/workspace/history">Open full history</Link></div>
    </section>
    <section className="panel"><h2>Specialist engines</h2><p className="sectionLead">Runs launched from this shell use <b>{workspace.name}</b> as the active workspace context. API authorization remains authoritative for every workspace-scoped resource.</p><div className="engineList">{engines.map(([id,n])=><Link href={`/workspace/engines/${id}`} className="engineLink" key={id}><b>{id} · {n}</b><span>Run a clearly labeled demonstration scenario or connect normalized provider evidence.</span></Link>)}</div></section>
    <div className="demoBanner" style={{marginTop:16}}>* All ten engines have non-demo provider-grounded or direct-state execution paths, but several remain PARTIAL without commercial credentials or protocol-native evidence. The UI does not fabricate connectivity or completeness.</div>
  </>;
}
