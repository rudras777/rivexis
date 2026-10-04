"use client";

import {useEffect,useRef,useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type Monitor={id:string;entity:string;chain:string;status:string;last_analysis_id?:string|null;last_status?:string|null};
type EngineResult={analysis_id:string;status:string;risk_score:number|null;severity:string;summary:string;signals:Array<Record<string,unknown>>;metrics:Record<string,unknown>;missing_data:string[]};
type CreateVars={workspaceId:string;entity:string;chain:string};
type CheckVars={workspaceId:string;id:string};

function monitorError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load this workspace's monitors.";
    if(error.status===403||error.status===404)return "Monitor access is unavailable because this workspace could not be authorized.";
    if(error.status===503)return "Monitor services are temporarily unavailable.";
  }
  return "Rivexis could not load monitors for this workspace.";
}

export default function Monitors(){
  const qc=useQueryClient();
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const [entity,setEntity]=useState("");
  const [chain,setChain]=useState("ethereum");
  const [latest,setLatest]=useState<EngineResult|null>(null);

  const list=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"monitors"),
    queryFn:()=>api<{items:Monitor[]}>(`/api/v1/monitors?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const create=useMutation({
    mutationFn:(vars:CreateVars)=>api<Monitor>("/api/v1/monitors",{method:"POST",body:JSON.stringify({entity:vars.entity,chain:vars.chain,rules:["balance_change","bytecode_change"],config:{balance_change_threshold_pct:20,supply_change_threshold_pct:5,oracle_change_threshold_pct:10,oracle_max_age_seconds:3600},workspace_id:vars.workspaceId})}),
    onSuccess:(_row,vars)=>{if(workspaceRef.current===vars.workspaceId)void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"monitors")});},
  });
  const check=useMutation({
    mutationFn:(vars:CheckVars)=>api<EngineResult>(`/api/v1/monitors/${vars.id}/check`,{method:"POST"}),
    onSuccess:(result,vars)=>{
      if(workspaceRef.current!==vars.workspaceId)return;
      setLatest(result);
      void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"monitors")});
    },
  });

  useEffect(()=>{
    workspaceRef.current=workspaceId;
    setLatest(null);
    create.reset();
    check.reset();
  },[workspaceId]);

  const monitors=list.data?.items??[];
  const validEntity=/^0x[a-fA-F0-9]{40}$/.test(entity.trim());
  const activeCount=monitors.filter(m=>m.status.toUpperCase()==="ACTIVE").length;
  const checkedCount=monitors.filter(m=>Boolean(m.last_analysis_id)).length;
  const missingData=latest?.missing_data??[];
  return <>
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">B3 operational workflow</div><h1>Threat monitors</h1><p>Store validated entities and run explicit on-demand B3 evidence requests without implying continuous surveillance or an RPC snapshot that did not occur.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name}</span><span className="badge">MANUAL POLLING</span></div></div>
    <section className="overviewBand surfaceOverview" aria-label="Monitor overview"><div><small>CONFIGURED</small><strong>{list.isPending?"—":monitors.length}</strong><span>Workspace monitors</span></div><div><small>ACTIVE</small><strong>{list.isPending?"—":activeCount}</strong><span>Enabled definitions</span></div><div><small>CHECKED</small><strong>{list.isPending?"—":checkedCount}</strong><span>With persisted B3 result</span></div><div><small>POLLING MODE</small><strong>01</strong><span>Manual, not continuous</span></div></section>
    <div className="truthNotice"><span className="statusDot"/>Each “Check now” action submits one non-demo B3 evidence request. The current free Edge runtime has no verified provider source configured, so it returns UNKNOWN rather than inventing a snapshot, signal, or continuous-monitoring claim.</div>
    <section className="panel operationalPanel"><div className="panelHeading"><div><span className="workspaceKicker">New definition</span><h2>Create monitor</h2></div><p className="sectionLead">The address must be a complete EVM address. Rule metadata is stored with the monitor definition; it is not represented as evaluated until a provider-backed B3 check actually produces evidence.</p></div><div className="surfaceFormGrid"><label className="field">Entity address<input aria-invalid={entity.length>0&&!validEntity} value={entity} onChange={e=>setEntity(e.target.value)} placeholder="0x… 40 hexadecimal characters"/><small>Wallet or contract address on the selected network.</small></label><label className="field">Network<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select><small>Evidence requests remain scoped to this chain.</small></label><button className="button formAction" type="button" disabled={create.isPending||!validEntity} onClick={()=>create.mutate({workspaceId,entity:entity.trim(),chain})}>{create.isPending?"Creating…":"Create monitor"}</button></div>{entity.length>0&&!validEntity?<p className="fieldError" role="status">Enter a full 0x-prefixed 20-byte EVM address.</p>:null}{create.isError?<p className="error" role="alert">Rivexis could not create this monitor. Review the address and retry.</p>:null}</section>
    <section className="panel operationalPanel" aria-live="polite" data-testid="workspace-monitors-state"><div className="panelHeading"><div><span className="workspaceKicker">Authorized inventory</span><h2>Configured monitors</h2></div><p className="sectionLead">Definitions and results shown here belong only to the active workspace.</p></div>{list.isPending?<div className="surfaceState" role="status">Loading monitors for {workspace.name}…</div>:null}{list.isError?<p className="error" role="alert">{monitorError(list.error)}</p>:null}{!list.isPending&&!list.isError&&!monitors.length?<div className="surfaceState"><b>No monitors are configured in this workspace yet.</b><span>Create the first validated definition above. Rivexis will not synthesize a check or status.</span></div>:null}{!list.isPending&&!list.isError&&monitors.length?<div className="tableWrap"><table className="table"><thead><tr><th>Entity</th><th>Network</th><th>Definition</th><th>Last B3 state</th><th>Action</th></tr></thead><tbody>{monitors.map(m=>{const checking=check.isPending&&check.variables?.id===m.id;return <tr key={m.id}><td><code>{m.entity}</code></td><td>{m.chain}</td><td><span className={`statePill ${m.status.toUpperCase()==="ACTIVE"?"positive":"neutral"}`}>{m.status}</span></td><td>{m.last_status?<span className="statePill neutral">{m.last_status}</span>:"Not checked"}</td><td><button className="ghost compactButton" type="button" disabled={check.isPending} onClick={()=>check.mutate({workspaceId,id:m.id})}>{checking?"Checking…":"Check now"}</button></td></tr>})}</tbody></table></div>:null}</section>
    {check.isError?<p className="error" role="alert">Rivexis could not complete the monitor check. Retry after confirming provider availability.</p>:null}
    {latest&&<section className="panel resultPanel" data-testid="monitor-latest-result"><div className="resultBanner isLive" role="status"><span className="statusDot"/>ON-DEMAND B3 RESULT · {workspace.name}</div><div className="resultHero"><div><span className="workspaceKicker">Latest evidence request</span><strong>{latest.status}</strong><p>{latest.summary}</p></div><div className="resultScore"><span>RISK SCORE</span><b>{latest.risk_score==null?"—":latest.risk_score}</b><small>{latest.risk_score==null?"":"/100"}</small></div></div><div className="resultGrid"><div><span>Severity</span><b>{latest.severity}</b></div><div><span>Signals</span><b>{latest.signals.length}</b></div><div><span>Missing data</span><b>{missingData.length}</b></div></div>{missingData.length?<section className="findingBlock" style={{marginTop:14}}><h3>Missing data</h3><ul>{missingData.map(item=><li key={item}>{item}</li>)}</ul></section>:null}<details className="advancedPayload"><summary>Inspect normalized B3 payload</summary><pre className="result">{JSON.stringify(latest,null,2)}</pre></details></section>}
  </>;
}