"use client";

import {useEffect,useRef,useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type Monitor={id:string;entity:string;chain:string;status:string;last_analysis_id?:string|null;last_status?:string|null};
type EngineResult={analysis_id:string;status:string;risk_score:number;severity:string;summary:string;signals:Array<Record<string,unknown>>;metrics:Record<string,unknown>;missing_data:string[]};
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
  const [entity,setEntity]=useState("0x1111111111111111111111111111111111111111");
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
  return <>
    <div className="workspaceHeader"><div><h1>Threat Monitors</h1><p>B3 stores point-in-time RPC snapshots and compares each manual check with the prior snapshot. This is not continuous Hypernative/Blockaid/WebSocket monitoring.</p></div><span className="badge">{workspace.name} · MANUAL POLLING</span></div>
    <section className="panel"><h2>Create monitor</h2><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Entity address<input value={entity} onChange={e=>setEntity(e.target.value)}/></label><label className="field">Chain<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label><button className="button" disabled={create.isPending} onClick={()=>create.mutate({workspaceId,entity,chain})}>{create.isPending?"Creating…":"Create"}</button></div>{create.isError?<p className="error" role="alert">Rivexis could not create this monitor. Review the input and retry.</p>:null}</section>
    <section className="panel" aria-live="polite" data-testid="workspace-monitors-state"><h2>Configured monitors</h2>{list.isPending?<p>Loading monitors for {workspace.name}…</p>:null}{list.isError?<p className="error" role="alert">{monitorError(list.error)}</p>:null}{!list.isPending&&!list.isError&&!monitors.length?<p>No monitors are configured in this workspace yet.</p>:null}{!list.isPending&&!list.isError&&monitors.length?<div className="tableWrap"><table className="table"><thead><tr><th>Entity</th><th>Chain</th><th>Status</th><th>Last B3 state</th><th></th></tr></thead><tbody>{monitors.map(m=><tr key={m.id}><td><code>{m.entity}</code></td><td>{m.chain}</td><td>{m.status}</td><td>{m.last_status??"Not checked"}</td><td><button className="button" disabled={check.isPending} onClick={()=>check.mutate({workspaceId,id:m.id})}>Check now</button></td></tr>)}</tbody></table></div>:null}</section>
    {check.isError?<p className="error" role="alert">Rivexis could not complete the monitor check. Retry after confirming provider availability.</p>:null}
    {latest&&<section className="panel" data-testid="monitor-latest-result"><h2>Latest B3 result · {workspace.name}</h2><p><b>{latest.status}</b> · risk {latest.risk_score}/100 · {latest.severity}</p><p>{latest.summary}</p><pre className="result">{JSON.stringify(latest,null,2)}</pre></section>}
  </>;
}
