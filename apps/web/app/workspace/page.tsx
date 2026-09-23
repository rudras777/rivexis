"use client";

import Link from "next/link";
import {useQuery} from "@tanstack/react-query";
import {api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

const engines=[['B1','Transaction Simulation'],['B2','Transaction & Contract Security'],['B3','Threat & Monitoring'],['B4','Entity & Fund Flow'],['B5','Cross-Chain Route'],['F1','Portfolio & Exposure'],['F2','Protocol Risk'],['F3','Position & Liquidation'],['F4','Yield & Strategy'],['F5','Treasury & Scenarios']];
type HistoryItem={type:"analysis"|"decision";id:string;workspace_id:string;engine_id?:string;demo?:boolean;created_at:string};
type SavedItem={id:string;analysis_id:string;title:string;archived:boolean;created_at:string};
type MonitorItem={id:string};
type RuntimeStat={logical_calls?:number};
type Runtime={providers:Record<string,RuntimeStat>};

function metric<T>(q:{isPending:boolean;isError:boolean;data?:T},read:(value:T)=>number){
  if(q.isPending)return "…";
  if(q.isError||!q.data)return "Unavailable";
  return String(read(q.data));
}

export default function Workspace(){
  const {workspaceId,workspace}=useWorkspace();
  const history=useQuery({queryKey:workspaceQueryKey(workspaceId,"dashboard-history"),queryFn:()=>api<{items:HistoryItem[]}>(`/api/v1/history?workspace_id=${encodeURIComponent(workspaceId)}&limit=50`),retry:false});
  const saved=useQuery({queryKey:workspaceQueryKey(workspaceId,"dashboard-saved"),queryFn:()=>api<{items:SavedItem[]}>(`/api/v1/saved-analyses?workspace_id=${encodeURIComponent(workspaceId)}`),retry:false});
  const monitors=useQuery({queryKey:workspaceQueryKey(workspaceId,"dashboard-monitors"),queryFn:()=>api<{items:MonitorItem[]}>(`/api/v1/monitors?workspace_id=${encodeURIComponent(workspaceId)}`),retry:false});
  const runtime=useQuery({queryKey:workspaceQueryKey(workspaceId,"dashboard-provider-runtime"),queryFn:()=>api<Runtime>(`/api/v1/providers/runtime?workspace_id=${encodeURIComponent(workspaceId)}`),retry:false});
  const recent=history.data?.items.slice(0,5)??[];

  return <>
    <div className="workspaceHeader"><div><h1>Rivexis Workspace</h1><p>Evidence → specialist engines → decision policy → explanation.</p></div><span className="badge">{workspace.name} · {workspace.access_role}</span></div>

    <section aria-labelledby="activity-heading">
      <h2 id="activity-heading" style={{fontSize:17}}>Workspace activity snapshot</h2>
      <p className="sectionLead">These values come from authorized API reads for <b>{workspace.name}</b>. “Unavailable” means Rivexis could not verify that metric; it is never converted to zero.</p>
      <div className="metricGrid" data-testid="workspace-activity-metrics">
        <div className="metricCard"><small>Recent history records</small><strong>{metric(history,d=>d.items.length)}</strong></div>
        <div className="metricCard"><small>Saved analyses</small><strong>{metric(saved,d=>d.items.length)}</strong></div>
        <div className="metricCard"><small>Configured monitors</small><strong>{metric(monitors,d=>d.items.length)}</strong></div>
        <div className="metricCard"><small>Recorded provider calls</small><strong>{metric(runtime,d=>Object.values(d.providers).reduce((sum,row)=>sum+(row.logical_calls??0),0))}</strong></div>
      </div>
    </section>

    <section className="panel" aria-live="polite" data-testid="workspace-recent-activity"><h2>Recent analysis & decision activity</h2>
      {history.isPending?<p>Loading recent activity for {workspace.name}…</p>:null}
      {history.isError?<p className="error" role="alert">Recent workspace activity is unavailable. Rivexis has not substituted cached or synthetic records.</p>:null}
      {!history.isPending&&!history.isError&&!recent.length?<p>No analysis or decision activity is recorded in this workspace yet.</p>:null}
      {!history.isPending&&!history.isError&&recent.length?<div className="tableWrap"><table className="table"><thead><tr><th>Time</th><th>Type</th><th>Engine</th><th>Mode</th><th>ID</th></tr></thead><tbody>{recent.map(row=><tr key={`${row.type}-${row.id}`}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.type}</td><td>{row.engine_id??"—"}</td><td>{row.type==="analysis"?(row.demo?"Demonstration":"Provider/direct-state"):"—"}</td><td><code>{row.id}</code></td></tr>)}</tbody></table></div>:null}
      <p style={{marginTop:12}}><Link className="ghost" href="/workspace/history">Open full history</Link></p>
    </section>

    <section className="panel"><h2>Platform capabilities <small style={{fontWeight:400}}>(static product metadata)</small></h2><p className="sectionLead">These counts describe Rivexis itself; they are not measurements of this workspace.</p><div className="metricGrid"><div className="metricCard"><small>Core engines</small><strong>10</strong></div><div className="metricCard"><small>Primary domains</small><strong>2</strong></div><div className="metricCard"><small>Decision states</small><strong>5</strong></div><div className="metricCard"><small>Provider-grounded paths</small><strong>10*</strong></div></div></section>

    <section className="panel"><h2>Specialist engines</h2><p className="sectionLead">Runs launched from this shell use <b>{workspace.name}</b> as the active workspace context. API authorization remains authoritative for every workspace-scoped resource.</p><div className="engineList">{engines.map(([id,n])=><Link href={`/workspace/engines/${id}`} className="engineLink" key={id}><b>{id} · {n}</b><span>Run a clearly labeled demonstration scenario or connect normalized provider evidence.</span></Link>)}</div></section>
    <div className="demoBanner" style={{marginTop:16}}>* All ten engines have non-demo provider-grounded or direct-state execution paths, but several remain PARTIAL without commercial credentials or protocol-native evidence. The UI does not fabricate connectivity or completeness.</div>
  </>;
}
