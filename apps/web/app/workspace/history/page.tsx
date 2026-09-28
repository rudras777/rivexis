"use client";

import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {useEffect,useMemo,useState} from "react";
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
type HistorySelection={type:"analysis"|"decision";id:string};
type Selection=HistorySelection|null;
type HistoryTypeFilter="all"|"analysis"|"decision";
type HistoryModeFilter="all"|"demo"|"non-demo";
type SavedAnalysis={id:string;workspace_id:string;analysis_id:string;title:string;archived:boolean;created_at:string};

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

function saveError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could save this analysis reference.";
    if(error.status===403||error.status===404)return "This analysis can no longer be saved from the active workspace.";
    if(error.status===422)return "Rivexis could not create a valid saved-analysis reference from this record.";
    if(error.status===503)return "Saving is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not save this analysis reference.";
}

function recordedAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}

function savedTitle(item:HistoryRow){
  const engine=item.engine_id?.trim()||"Analysis";
  const date=new Date(item.created_at);
  const when=Number.isNaN(date.getTime())?item.created_at:date.toLocaleDateString();
  return `${engine} analysis · ${when}`;
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
  const queryClient=useQueryClient();
  const savedQueryKey=workspaceQueryKey(workspaceId,"saved-analyses",true);
  const [selected,setSelected]=useState<Selection>(null);
  const [search,setSearch]=useState("");
  const [typeFilter,setTypeFilter]=useState<HistoryTypeFilter>("all");
  const [modeFilter,setModeFilter]=useState<HistoryModeFilter>("all");
  const [notice,setNotice]=useState("");

  useEffect(()=>{
    setSelected(null);
    setSearch("");
    setTypeFilter("all");
    setModeFilter("all");
    setNotice("");
  },[workspaceId]);

  const q=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"history"),
    queryFn:()=>api<{items:HistoryRow[]}>(`/api/v1/history?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const saved=useQuery({
    queryKey:savedQueryKey,
    queryFn:()=>api<{items:SavedAnalysis[]}>(`/api/v1/saved-analyses?workspace_id=${encodeURIComponent(workspaceId)}&include_archived=true`),
    retry:false,
  });
  const detail=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"history-provenance",selected?.type??"none",selected?.id??"none"),
    queryFn:()=>api<Detail>(selected?.type==="analysis"?`/api/v1/analyses/${encodeURIComponent(selected.id)}`:`/api/v1/decisions/${encodeURIComponent(selected!.id)}`),
    enabled:Boolean(selected),
    retry:false,
  });

  const save=useMutation({
    mutationFn:(item:HistoryRow)=>api<SavedAnalysis>("/api/v1/saved-analyses",{method:"POST",body:JSON.stringify({analysis_id:item.id,title:savedTitle(item)})}),
    onSuccess:(saved)=>{
      setNotice(`Saved ${saved.analysis_id} as “${saved.title}”.`);
      queryClient.setQueryData<{items:SavedAnalysis[]}>(savedQueryKey,current=>({items:[...(current?.items??[]).filter(item=>item.analysis_id!==saved.analysis_id),saved]}));
      queryClient.invalidateQueries({queryKey:workspaceQueryKey(workspaceId,"saved-analyses")});
    },
  });

  const items=q.data?.items??[];
  const savedAnalysisIds=useMemo(()=>new Set((saved.data?.items??[]).map(item=>item.analysis_id)),[saved.data?.items]);
  const filtered=useMemo(()=>{
    const needle=search.trim().toLowerCase();
    return items.filter(item=>{
      if(typeFilter!=="all"&&item.type!==typeFilter)return false;
      if(modeFilter!=="all"){
        if(item.type!=="analysis")return false;
        if(modeFilter==="demo"&&item.demo!==true)return false;
        if(modeFilter==="non-demo"&&item.demo===true)return false;
      }
      if(!needle)return true;
      const mode=item.type==="analysis"?(item.demo?"demo demonstration":"non-demo live"):"decision";
      return `${item.type} ${item.id} ${item.engine_id??""} ${mode}`.toLowerCase().includes(needle);
    });
  },[items,search,typeFilter,modeFilter]);

  function inspect(item:HistoryRow){
    if(item.type!=="analysis"&&item.type!=="decision")return;
    const next:HistorySelection={type:item.type,id:item.id};
    setSelected(current=>current?.type===next.type&&current.id===next.id?null:next);
  }

  return <>
    <div className="workspaceHeader"><div><h1>History</h1><p>Search, inspect and retain canonical analyses and decisions for the active workspace.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel" aria-live="polite" data-testid="workspace-history-state">
      <div className="surfaceToolbar">
        <label className="field"><span>Search</span><input aria-label="Search history" value={search} onChange={event=>setSearch(event.target.value)} placeholder="Reference, engine or record type"/></label>
        <label className="field"><span>Record type</span><select aria-label="History record type" value={typeFilter} onChange={event=>setTypeFilter(event.target.value as HistoryTypeFilter)}><option value="all">All records</option><option value="analysis">Analyses</option><option value="decision">Decisions</option></select></label>
        <label className="field"><span>Analysis mode</span><select aria-label="History analysis mode" value={modeFilter} onChange={event=>setModeFilter(event.target.value as HistoryModeFilter)}><option value="all">All modes</option><option value="demo">Demonstration</option><option value="non-demo">Non-demo</option></select></label>
      </div>

      {notice?<p className="success" role="status">{notice}</p>:null}
      {save.error?<p className="error" role="alert">{saveError(save.error)}</p>:null}
      {q.isPending?<p>Loading history for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{historyError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>No analyses or decisions are recorded in this workspace yet.</p>:null}
      {!q.isPending&&!q.isError&&items.length&&!filtered.length?<p>No history records match the current search and filters.</p>:null}
      {!q.isPending&&!q.isError&&filtered.length?<><p className="sectionLead">Showing {filtered.length} of {items.length} records from the API&apos;s recent-history window. Canonical provenance is loaded on demand. Saving an analysis creates a durable reference without copying or deleting the underlying history record.</p><div className="tableWrap"><table className="table"><thead><tr><th>Type</th><th>Reference</th><th>Engine</th><th>Mode</th><th>Recorded</th><th>Actions</th></tr></thead><tbody>{filtered.map(item=>{
        const isSelected=selected?.type===item.type&&selected.id===item.id;
        const inspectable=item.type==="analysis"||item.type==="decision";
        const saving=save.isPending&&save.variables?.id===item.id;
        const isSaved=item.type==="analysis"&&savedAnalysisIds.has(item.id);
        return <tr key={`${item.type}-${item.id}`}><td>{item.type}</td><td><code>{item.id}</code></td><td>{item.engine_id??"—"}</td><td>{item.type==="analysis"?(item.demo?"Demo":"Non-demo"):"—"}</td><td>{recordedAt(item.created_at)}</td><td><div className="actions">{inspectable?<button className="ghost" onClick={()=>inspect(item)} aria-expanded={isSelected}>{isSelected?"Hide provenance":"Inspect provenance"}</button>:null}{item.type==="analysis"?<button className={isSaved?"ghost":"button"} disabled={saving||isSaved} onClick={()=>save.mutate(item)}>{saving?"Saving…":isSaved?"Saved":"Save reference"}</button>:null}{!inspectable?"—":null}</div></td></tr>;
      })}</tbody></table></div></>:null}
    </section>
    {selected?<section className="panel" aria-live="polite" data-testid="history-provenance-detail">
      {detail.isPending?<p>Loading canonical provenance for <code>{selected.id}</code>…</p>:null}
      {detail.isError?<p className="error" role="alert">{detailError(detail.error)}</p>:null}
      {detail.data?(selected.type==="analysis"?<AnalysisProvenance detail={detail.data}/>:<DecisionProvenance detail={detail.data}/>):null}
    </section>:null}
  </>;
}
