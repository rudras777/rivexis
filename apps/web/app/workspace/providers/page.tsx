"use client";

import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type P={provider_id:string;status:string;configured:boolean;detail?:string;latency_ms?:number;chain_id?:number;block_number?:number};
type RuntimeStat={logical_calls?:number;attempts?:number;successes?:number;failures?:number;cache_hits?:number;circuit?:{state?:string}};
type Runtime={scope:string;control_backend:string;providers:Record<string,RuntimeStat>};
type Registry={chain:string;deep_probe_available?:boolean;providers:P[]};

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
    queryFn:()=>api<Registry>(`/api/v1/providers/status?chain=${encodeURIComponent(chain)}&deep=${deep}`),
    retry:false,
  });
  const runtime=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"provider-runtime"),
    queryFn:()=>api<Runtime>(`/api/v1/providers/runtime?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const runtimeEntries=Object.entries(runtime.data?.providers??{});
  const deepProbeAvailable=registry.data?.deep_probe_available===true&&Boolean(registry.data.providers.some(provider=>provider.configured));
  const providers=registry.data?.providers??[];
  const configuredCount=providers.filter(provider=>provider.configured).length;
  const healthyCount=providers.filter(provider=>["HEALTHY","AVAILABLE","READY","OK"].includes(provider.status.toUpperCase())).length;
  const logicalCalls=runtimeEntries.reduce((total,[,stat])=>total+(stat.logical_calls??0),0);

  return <>
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">Infrastructure control plane</div><h1>Provider health</h1><p>Separate shared provider configuration from workspace-attributed runtime activity.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name}</span><span className="badge">GLOBAL + WORKSPACE</span></div></div>
    <section className="overviewBand surfaceOverview" aria-label="Provider operational overview">
      <div><small>REGISTRY ENTRIES</small><strong>{registry.isPending?"—":providers.length}</strong><span>{chain} infrastructure</span></div>
      <div><small>CONFIGURED</small><strong>{registry.isPending?"—":configuredCount}</strong><span>Does not imply connectivity</span></div>
      <div><small>HEALTHY PROBES</small><strong>{registry.isPending?"—":healthyCount}</strong><span>{deep?"Deep-probe view":"Configuration view"}</span></div>
      <div><small>WORKSPACE CALLS</small><strong>{runtime.isPending?"—":logicalCalls}</strong><span>Active workspace only</span></div>
    </section>
    <section className="panel operationalPanel">
      <div className="panelHeading"><div><span className="workspaceKicker">Shared infrastructure</span><h2>Global provider registry</h2></div><p className="sectionLead">Configuration is application-wide. It never proves that a request succeeded or that decision-grade evidence exists.</p></div>
      <div className="surfaceToolbar">
        <label className="field compactField">Network<select aria-label="Provider network" value={chain} onChange={e=>{setChain(e.target.value);setDeep(false)}}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label>
        <div className="toolbarActions">
          <button className="ghost" type="button" onClick={()=>void registry.refetch()} disabled={registry.isFetching}>{registry.isFetching?"Refreshing…":"Refresh status"}</button>
          {deepProbeAvailable?<button className="button" type="button" onClick={()=>setDeep(v=>!v)}>{deep?"Return to configuration":"Run deep RPC probe"}</button>:null}
        </div>
      </div>
      {!registry.isPending&&!deepProbeAvailable?<div className="truthNotice" role="status"><span className="statusDot"/>Deep provider probes are not available on this runtime. Rivexis is showing configuration state only and will not imply live connectivity.</div>:null}
      <div className="tableWrap surfaceTable">
        {registry.isPending?<div className="surfaceState" role="status">Loading the provider registry…</div>:null}
        {registry.isError?<p className="error" role="alert">{genericError(registry.error,"registry")}</p>:null}
        {!registry.isPending&&!registry.isError&&!providers.length?<div className="surfaceState"><b>No registry entries returned</b><span>This network has no provider configuration exposed by the runtime.</span></div>:null}
        {!registry.isPending&&!registry.isError&&providers.length?<table className="table"><thead><tr><th>Provider</th><th>State</th><th>Configuration</th><th>Latency</th><th>Evidence block</th></tr></thead><tbody>{providers.map(p=><tr key={p.provider_id}><td><b>{p.provider_id}</b></td><td><span className={`statePill ${["HEALTHY","AVAILABLE","READY","OK"].includes(p.status.toUpperCase())?"positive":p.status.toUpperCase()==="UNCONFIGURED"?"neutral":"warning"}`}>{p.status}</span></td><td>{p.configured?"Configured":"Not configured"}</td><td>{p.latency_ms!=null?`${p.latency_ms} ms`:"—"}</td><td>{p.block_number??"—"}</td></tr>)}</tbody></table>:null}
      </div>
    </section>
    <section className="panel operationalPanel" aria-live="polite" data-testid="workspace-provider-runtime">
      <div className="panelHeading"><div><span className="workspaceKicker">Tenant-scoped telemetry</span><h2>Workspace runtime · {workspace.name}</h2></div><p className="sectionLead">Only calls attributed to this workspace appear here. No activity is synthesized when a provider-backed path has not run.</p></div>
      {runtime.isPending?<div className="surfaceState" role="status">Loading workspace provider telemetry…</div>:null}
      {runtime.isError?<p className="error" role="alert">{genericError(runtime.error,"runtime")}</p>:null}
      {!runtime.isPending&&!runtime.isError&&!runtimeEntries.length?<div className="surfaceState"><b>No provider runtime activity is recorded in this workspace yet.</b><span>The current free Edge runtime has no configured provider-backed engine path, so no provider calls are expected here. Telemetry will appear only after a verified provider integration is configured and exercised.</span></div>:null}
      {!runtime.isPending&&!runtime.isError&&runtimeEntries.length?<><div className="surfaceMeta"><span>Control backend</span><b>{runtime.data?.control_backend??"unknown"}</b></div><div className="tableWrap"><table className="table"><thead><tr><th>Provider</th><th>Logical calls</th><th>Attempts</th><th>Successes</th><th>Failures</th><th>Cache hits</th><th>Circuit</th></tr></thead><tbody>{runtimeEntries.map(([provider,stat])=><tr key={provider}><td><b>{provider}</b></td><td>{stat.logical_calls??0}</td><td>{stat.attempts??0}</td><td>{stat.successes??0}</td><td>{stat.failures??0}</td><td>{stat.cache_hits??0}</td><td><span className={`statePill ${(stat.circuit?.state??"").toUpperCase()==="CLOSED"?"positive":"neutral"}`}>{stat.circuit?.state??"UNKNOWN"}</span></td></tr>)}</tbody></table></div></>:null}
    </section>
  </>;
}