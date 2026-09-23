"use client";

import {useQuery} from "@tanstack/react-query";
import {useEffect,useState} from "react";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type HistoryRow={
  type:"analysis"|"decision"|string;
  id:string;
  workspace_id:string;
  engine_id?:string|null;
  demo?:boolean|null;
  created_at:string;
};
type Selection={type:"analysis"|"decision";id:string}|null;

type Detail=Record<string,unknown>;

function historyError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load this workspace history.";
    if(error.status===403||error.status===404)return "History is unavailable because access to this workspace could not be confirmed.";
    if(error.status===503)return "History is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load history for this workspace.";
}

function detailError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load this persisted record.";
    if(error.status===403||error.status===404)return "This persisted record is unavailable in the active workspace.";
    if(error.status===503)return "Record provenance is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load provenance for this persisted record.";
}

function recordedAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}

function text(value:unknown,fallback="—"){
  return typeof value==="string"&&value.trim()?value:fallback;
}
function numberText(value:unknown,suffix=""){
  return typeof value==="number"&&Number.isFinite(value)?`${value}${suffix}`:"—";
}
function stringList(value:unknown){
  return Array.isArray(value)?value.filter((item):item is string=>typeof item==="string"&&Boolean(item.trim())):[];
}
function record(value:unknown){
  return value&&typeof value==="object"&&!Array.isArray(value)?value as Record<string,unknown>:{};
}
function evidenceMetadata(value:unknown){
  if(!Array.isArray(value))return {count:0,providers:[] as string[],sourceTypes:[] as string[]};
  const rows=value.filter((item):item is Record<string,unknown>=>Boolean(item)&&typeof item==="object"&&!Array.isArray(item));
  const providers=[...new Set(rows.map(item=>item.provider).filter((item):item is string=>typeof item==="string"&&Boolean(item.trim())))].sort();
  const sourceTypes=[...new Set(rows.map(item=>item.source_type).filter((item):item is string=>typeof item==="string"&&Boolean(item.trim())))].sort();
  return {count:rows.length,providers,sourceTypes};
}

function KeyValueTable({rows}:{rows:Array<[string,string]>}){
  return <div className="tableWrap"><table className="table"><tbody>{rows.map(([label,value])=><tr key={label}><th scope="row">{label}</th><td>{value}</td></tr>)}</tbody></table></div>;
}

function AnalysisProvenance({detail}:{detail:Detail}){
  const evidence=evidenceMetadata(detail.evidence);
  const missing=stringList(detail.missing_data);
  const conflicts=Array.isArray(detail.provider_conflicts)?detail.provider_conflicts.length:0;
  const rows:Array<[string,string]>=[
    ["Status",text(detail.status,"UNKNOWN")],
    ["Engine",text(detail.engine_id)],
    ["Engine version",text(detail.engine_version)],
    ["Analysis framework",text(detail.analysis_framework_version)],
    ["Mode",detail.demo===true?"Demonstration":"Non-demo"],
    ["Risk score",numberText(detail.risk_score,"/100")],
    ["Data confidence",numberText(detail.data_confidence,"%")],
    ["Engine confidence",numberText(detail.engine_confidence,"%")],
    ["Provider consensus",text(detail.provider_consensus,"UNAVAILABLE")],
    ["Evidence records",String(evidence.count)],
    ["Evidence providers",evidence.providers.join(", ")||"None recorded"],
    ["Evidence source types",evidence.sourceTypes.join(", ")||"None recorded"],
    ["Unresolved source conflicts",String(conflicts)],
  ];
  return <>
    <h3>Persisted analysis provenance</h3>
    <KeyValueTable rows={rows}/>
    {missing.length>0?<><h4>Missing data</h4><ul>{missing.map(item=><li key={item}>{item}</li>)}</ul></>:<p className="muted">No missing-data entries are recorded in this persisted result.</p>}
  </>;
}

function DecisionProvenance({detail}:{detail:Detail}){
  const engineStatuses=record(detail.engine_statuses);
  const engineVersions=record(detail.engine_versions);
  const frameworkVersions=record(detail.analysis_framework_versions);
  const engines=[...new Set([...Object.keys(engineStatuses),...Object.keys(engineVersions),...Object.keys(frameworkVersions)])].sort();
  const sources=stringList(detail.evidence_sources);
  const analysisIds=stringList(detail.analysis_ids);
  const rows:Array<[string,string]>=[
    ["Decision",text(detail.decision,"UNKNOWN")],
    ["Decision methodology",text(detail.decision_methodology_version)],
    ["Canonical persisted inputs",detail.canonical_persistence_verified===true?"Verified":"Not verified"],
    ["Decision confidence",numberText(detail.decision_confidence,"%")],
    ["Data confidence",numberText(detail.data_confidence,"%")],
    ["Evidence records",numberText(detail.evidence_count)],
    ["Evidence providers",sources.join(", ")||"None recorded"],
    ["Unresolved source conflicts",numberText(detail.unresolved_conflict_count)],
  ];
  return <>
    <h3>Persisted decision provenance</h3>
    <KeyValueTable rows={rows}/>
    <h4>Specialist inputs</h4>
    {engines.length?<div className="tableWrap"><table className="table"><thead><tr><th>Engine</th><th>Status</th><th>Engine version</th><th>Framework</th></tr></thead><tbody>{engines.map(engine=><tr key={engine}><td>{engine}</td><td>{text(engineStatuses[engine],"UNKNOWN")}</td><td>{text(engineVersions[engine])}</td><td>{text(frameworkVersions[engine])}</td></tr>)}</tbody></table></div>:<p className="muted">No specialist engine provenance is recorded.</p>}
    <h4>Persisted analysis references</h4>
    {analysisIds.length?<ul>{analysisIds.map(id=><li key={id}><code>{id}</code></li>)}</ul>:<p className="muted">No analysis references are recorded.</p>}
  </>;
}

export default function History(){
  const {workspaceId,workspace}=useWorkspace();
  const [selected,setSelected]=useState<Selection>(null);
  useEffect(()=>setSelected(null),[workspaceId]);
  const q=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"history"),
    queryFn:()=>api<{items:HistoryRow[]}>(`/api/v1/history?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const detail=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"history-provenance",selected?.type??"none",selected?.id??"none"),
    queryFn:()=>api<Detail>(selected?.type==="analysis"?`/api/v1/analyses/${encodeURIComponent(selected.id)}`:`/api/v1/decisions/${encodeURIComponent(selected!.id)}`),
    enabled:Boolean(selected),
    retry:false,
  });
  const items=q.data?.items??[];
  function inspect(item:HistoryRow){
    if(item.type!=="analysis"&&item.type!=="decision")return;
    setSelected(current=>current?.type===item.type&&current.id===item.id?null:{type:item.type,id:item.id});
  }
  return <>
    <div className="workspaceHeader"><div><h1>History</h1><p>Analyses and decisions retained for the active workspace only.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel" aria-live="polite" data-testid="workspace-history-state">
      {q.isPending?<p>Loading history for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{historyError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>No analyses or decisions are recorded in this workspace yet.</p>:null}
      {!q.isPending&&!q.isError&&items.length?<><p className="sectionLead">The API returns at most 50 recent records. This table does not imply a lifetime total. Provenance is loaded on demand from the authorized persisted record, not inferred from this summary list.</p><div className="tableWrap"><table className="table"><thead><tr><th>Type</th><th>Reference</th><th>Engine</th><th>Mode</th><th>Recorded</th><th>Provenance</th></tr></thead><tbody>{items.map(item=>{
        const isSelected=selected?.type===item.type&&selected.id===item.id;
        const inspectable=item.type==="analysis"||item.type==="decision";
        return <tr key={`${item.type}-${item.id}`}><td>{item.type}</td><td><code>{item.id}</code></td><td>{item.engine_id??"—"}</td><td>{item.type==="analysis"?(item.demo?"Demo":"Non-demo"):"—"}</td><td>{recordedAt(item.created_at)}</td><td>{inspectable?<button className="button" onClick={()=>inspect(item)} aria-expanded={isSelected}>{isSelected?"Hide":"Inspect"}</button>:"—"}</td></tr>;
      })}</tbody></table></div></>:null}
    </section>
    {selected?<section className="panel" aria-live="polite" data-testid="history-provenance-detail">
      {detail.isPending?<p>Loading canonical provenance for <code>{selected.id}</code>…</p>:null}
      {detail.isError?<p className="error" role="alert">{detailError(detail.error)}</p>:null}
      {detail.data?(selected.type==="analysis"?<AnalysisProvenance detail={detail.data}/>:<DecisionProvenance detail={detail.data}/>):null}
    </section>:null}
  </>;
}
