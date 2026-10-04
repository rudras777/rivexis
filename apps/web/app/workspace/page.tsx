"use client";

import Link from "next/link";
import {useQuery} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

const engines=[['B1','Transaction Simulation','Execution'],['B2','Transaction & Contract Security','Security'],['B3','Threat & Monitoring','Monitoring'],['B4','Entity & Fund Flow','Entities'],['B5','Cross-Chain Route','Routing'],['F1','Portfolio & Exposure','Portfolio'],['F2','Protocol Risk','Protocols'],['F3','Position & Liquidation','Positions'],['F4','Yield & Strategy','Yield'],['F5','Treasury & Scenarios','Treasury']];

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
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">Decision intelligence workspace</div><h1>Good {new Date().getHours()<12?"morning":new Date().getHours()<18?"afternoon":"evening"}.</h1><p>Move from attributed evidence to a defensible decision.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name} · {workspace.access_role}</span><Link className="button" href="/workspace/engines/B1">Run analysis <span aria-hidden="true">↗</span></Link></div></div>
    <section className="metadataIntro"><div><span className="workspaceKicker">Capability context</span><h2>Product metadata</h2></div><p>These values describe the Rivexis product surface. They are not live activity totals for {workspace.name}.</p></section>
    <section className="overviewBand" aria-label="Product capability overview"><div><small>CORE ENGINES</small><strong>10</strong><span>B1–B5 · F1–F5</span></div><div><small>INTELLIGENCE DOMAINS</small><strong>02</strong><span>Blockchain · Finance</span></div><div><small>DECISION STATES</small><strong>05</strong><span>Explicit · deterministic</span></div><div><small>EVIDENCE POLICY</small><strong>0</strong><span>Fabricated signals</span></div></section>
    <section className="panel" aria-live="polite" data-testid="workspace-dashboard-activity">
      <h2>Recent workspace activity · {workspace.name}</h2>
      <p className="sectionLead">This list is loaded from the authorized history API for the active workspace only. It shows up to six recent analysis or decision records.</p>
      {activity.isPending?<p>Loading recent workspace activity…</p>:null}
      {activity.isError?<p className="error" role="alert">{activityError(activity.error)}</p>:null}
      {!activity.isPending&&!activity.isError&&!items.length?<p>No analysis or decision activity is recorded in this workspace yet.</p>:null}
      {!activity.isPending&&!activity.isError&&items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Type</th><th>Engine</th><th>Mode</th><th>Recorded</th></tr></thead><tbody>{items.map(item=><tr key={`${item.type}-${item.id}`}><td>{item.type}</td><td>{item.engine_id??"—"}</td><td>{item.type==="analysis"?(item.demo?"Demo":"Non-demo request"):"—"}</td><td>{recordedAt(item.created_at)}</td></tr>)}</tbody></table></div>:null}
      <div className="panelFooter"><span>Showing up to six authorized records</span><Link className="textLink" href="/workspace/history">Open full history <span aria-hidden="true">→</span></Link></div>
    </section>
    <section className="panel enginePanel"><div className="panelHeading"><div><span className="workspaceKicker">Analysis suite</span><h2>Specialist engines</h2></div><p className="sectionLead">Every run is isolated to <b>{workspace.name}</b> and retains evidence provenance.</p></div><div className="engineList">{engines.map(([id,n,domain])=><Link href={`/workspace/engines/${id}`} className="engineLink" key={id}><div className="engineMonogram">{id}</div><div><b>{n}</b><span>{domain} intelligence</span></div><span className="engineArrow" aria-hidden="true">↗</span></Link>)}</div></section>
    <div className="demoBanner" style={{marginTop:16}}>* Demonstration mode is synthetic and clearly labelled. The current production Edge runtime accepts non-demo evidence requests but returns UNKNOWN when verified provider evidence is unavailable; Rivexis does not invent provider connectivity or completeness.</div>
  </>;
}
