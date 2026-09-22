"use client";

import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type P={provider_id:string;status:string;configured:boolean;detail?:string;latency_ms?:number;chain_id?:number;block_number?:number};
type RuntimeStat={logical_calls?:number;attempts?:number;successes?:number;failures?:number;cache_hits?:number;circuit?:{state?:string}};
type Runtime={scope:string;control_backend:string;providers:Record<string,RuntimeStat>};

function genericError(error:unknown,kind:"registry"|"runtime"){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load provider state.";
    if(error.status===403||error.status===404)return kind==="runtime"?"Workspace provider telemetry is unavailable because access could not be confirmed.":"Provider health is unavailable for this session.";
    if(error.status===503)return "Provider state is temporarily unavailable because the application API is unavailable.";
  }
  return kind==="runtime"?"Rivexis could not load provider runtime telemetry for this workspace.":"Rivexis could not load the provider registry.";
}

export default function Providers(){
  const {workspaceId,workspace}=useWorkspace();
  const [chain,setChain]=useState("ethereum");
  const [deep,setDeep]=useState(false);
  const registry=useQuery({
    queryKey:["providers-global",chain,deep],
    queryFn:()=>api<{chain:string;providers:P[]}>(`/api/v1/providers/status?chain=${encodeURIComponent(chain)}&deep=${deep}`),
    retry:false,
  });
  const runtime=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"provider-runtime"),
    queryFn:()=>api<Runtime>(`/api/v1/providers/runtime?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const runtimeEntries=Object.entries(runtime.data?.providers??{});

  return <>
    <div className="workspaceHeader"><div><h1>Provider Health</h1><p>Global configuration health and workspace runtime telemetry are intentionally separate. A workspace switch never implies that shared provider credentials or global connectivity changed.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel">
      <h2>Global provider registry</h2>
      <p className="sectionLead">This is shared application infrastructure, not workspace-owned data. Deep probe performs a real JSON-RPC chain check only for configured RPC providers.</p>
      <div style={{display:"flex",gap:12,alignItems:"end",flexWrap:"wrap",marginTop:12}}>
        <label className="field" style={{maxWidth:260}}>Chain<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label>
        <button className="button" onClick={()=>setDeep(v=>!v)}>{deep?"Use configuration view":"Run deep RPC probe"}</button>
      </div>
      <div className="tableWrap" style={{marginTop:16}}>
        {registry.isPending?<p>Loading provider registry…</p>:null}
        {registry.isError?<p className="error" role="alert">{genericError(registry.error,"registry")}</p>:null}
        {!registry.isPending&&!registry.isError&&!registry.data?.providers.length?<p>No provider registry entries were returned for this chain.</p>:null}
        {!registry.isPending&&!registry.isError&&registry.data?.providers.length?<table className="table"><thead><tr><th>Provider</th><th>Status</th><th>Configured</th><th>Latency</th><th>Block</th></tr></thead><tbody>{registry.data.providers.map(p=><tr key={p.provider_id}><td>{p.provider_id}</td><td>{p.status}</td><td>{p.configured?"Yes":"No"}</td><td>{p.latency_ms!=null?`${p.latency_ms} ms`:"—"}</td><td>{p.block_number??"—"}</td></tr>)}</tbody></table>:null}
      </div>
    </section>
    <section className="panel" aria-live="polite" data-testid="workspace-provider-runtime">
      <h2>Workspace runtime · {workspace.name}</h2>
      <p className="sectionLead">Only provider calls attributed to the active workspace appear here. No activity is synthesized when the workspace has not executed a provider-backed path.</p>
      {runtime.isPending?<p>Loading workspace provider telemetry…</p>:null}
      {runtime.isError?<p className="error" role="alert">{genericError(runtime.error,"runtime")}</p>:null}
      {!runtime.isPending&&!runtime.isError&&!runtimeEntries.length?<p>No provider runtime activity is recorded in this workspace yet.</p>:null}
      {!runtime.isPending&&!runtime.isError&&runtimeEntries.length?<><p><b>Control backend:</b> {runtime.data?.control_backend??"unknown"}</p><div className="tableWrap"><table className="table"><thead><tr><th>Provider</th><th>Logical calls</th><th>Attempts</th><th>Successes</th><th>Failures</th><th>Cache hits</th><th>Circuit</th></tr></thead><tbody>{runtimeEntries.map(([provider,stat])=><tr key={provider}><td>{provider}</td><td>{stat.logical_calls??0}</td><td>{stat.attempts??0}</td><td>{stat.successes??0}</td><td>{stat.failures??0}</td><td>{stat.cache_hits??0}</td><td>{stat.circuit?.state??"UNKNOWN"}</td></tr>)}</tbody></table></div></>:null}
    </section>
  </>;
}
