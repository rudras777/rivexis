"use client";

import {useState} from "react";
import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {activeWorkspaceId,api} from "@/lib/api";

type Monitor={
  id:string;
  entity:string;
  chain:string;
  status:string;
  last_analysis_id?:string|null;
  last_status?:string|null;
};

type EngineResult={analysis_id:string;status:string;risk_score:number;severity:string;summary:string;signals:Array<Record<string,unknown>>;metrics:Record<string,unknown>;missing_data:string[]};

export default function Monitors(){
  const qc=useQueryClient();
  const [entity,setEntity]=useState("0x1111111111111111111111111111111111111111");
  const [chain,setChain]=useState("ethereum");
  const [latest,setLatest]=useState<EngineResult|null>(null);
  const list=useQuery({queryKey:["monitors"],queryFn:()=>api<{items:Monitor[]}>(`/api/v1/monitors${activeWorkspaceId()?`?workspace_id=${activeWorkspaceId()}`:""}`)});
  const create=useMutation({
    mutationFn:()=>api<Monitor>("/api/v1/monitors",{method:"POST",body:JSON.stringify({entity,chain,rules:["balance_change","bytecode_change"],config:{balance_change_threshold_pct:20,supply_change_threshold_pct:5,oracle_change_threshold_pct:10,oracle_max_age_seconds:3600},workspace_id:activeWorkspaceId()})}),
    onSuccess:()=>qc.invalidateQueries({queryKey:["monitors"]})
  });
  const check=useMutation({
    mutationFn:(id:string)=>api<EngineResult>(`/api/v1/monitors/${id}/check`,{method:"POST"}),
    onSuccess:(r)=>{setLatest(r);qc.invalidateQueries({queryKey:["monitors"]});}
  });
  return <>
    <div className="workspaceHeader"><div><h1>Threat Monitors</h1><p>B3 stores point-in-time RPC snapshots and compares each manual check with the prior snapshot. This is not continuous Hypernative/Blockaid/WebSocket monitoring.</p></div><span className="badge">MANUAL POLLING</span></div>
    <section className="panel"><h2>Create monitor</h2><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Entity address<input value={entity} onChange={e=>setEntity(e.target.value)}/></label><label className="field">Chain<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label><button className="button" disabled={create.isPending} onClick={()=>create.mutate()}>{create.isPending?"Creating…":"Create"}</button></div>{create.error&&<p className="error">{(create.error as Error).message}</p>}</section>
    <section className="panel"><h2>Configured monitors</h2><div className="tableWrap"><table className="table"><thead><tr><th>Entity</th><th>Chain</th><th>Status</th><th>Last B3 state</th><th></th></tr></thead><tbody>{list.data?.items.map(m=><tr key={m.id}><td><code>{m.entity}</code></td><td>{m.chain}</td><td>{m.status}</td><td>{m.last_status??"Not checked"}</td><td><button className="button" disabled={check.isPending} onClick={()=>check.mutate(m.id)}>Check now</button></td></tr>)}</tbody></table>{list.isLoading&&<p>Loading monitors…</p>}{list.error&&<p className="error">{(list.error as Error).message}</p>}</div></section>
    {latest&&<section className="panel"><h2>Latest B3 result</h2><p><b>{latest.status}</b> · risk {latest.risk_score}/100 · {latest.severity}</p><p>{latest.summary}</p><pre className="result">{JSON.stringify(latest,null,2)}</pre></section>}
  </>;
}
