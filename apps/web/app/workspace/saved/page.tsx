"use client";

import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {useEffect,useMemo,useRef,useState} from "react";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type SavedAnalysis={
  id:string;
  workspace_id:string;
  analysis_id:string;
  title:string;
  archived:boolean;
  created_at:string;
};

type Detail=Record<string,unknown>;
type ArchiveVars={workspaceId:string;id:string;archived:boolean};
type RemoveVars={workspaceId:string;id:string;analysisId:string};

function savedError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load saved analyses.";
    if(error.status===403||error.status===404)return "Saved analyses are unavailable because access to this workspace could not be confirmed.";
    if(error.status===503)return "Saved analyses are temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load saved analyses for this workspace.";
}

function detailError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load this persisted analysis.";
    if(error.status===403||error.status===404)return "This saved analysis no longer resolves to an authorized persisted analysis.";
    if(error.status===503)return "Analysis evidence is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load this saved analysis.";
}

function actionError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before the saved-analysis action could complete.";
    if(error.status===403||error.status===404)return "This saved analysis is no longer available in the active workspace.";
    if(error.status===503)return "The saved-analysis action is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not complete the saved-analysis action.";
}

function savedAt(value:string){
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

function evidenceCount(value:unknown){
  return Array.isArray(value)?value.length:0;
}

export default function Saved(){
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const queryClient=useQueryClient();
  const [includeArchived,setIncludeArchived]=useState(false);
  const [search,setSearch]=useState("");
  const [selected,setSelected]=useState<string|null>(null);
  const [deleteConfirm,setDeleteConfirm]=useState<string|null>(null);
  const [notice,setNotice]=useState("");

  const q=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"saved-analyses",includeArchived),
    queryFn:()=>api<{items:SavedAnalysis[]}>(`/api/v1/saved-analyses?workspace_id=${encodeURIComponent(workspaceId)}&include_archived=${includeArchived}`),
    retry:false,
  });

  const detail=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"saved-analysis-detail",selected??"none"),
    queryFn:()=>api<Detail>(`/api/v1/analyses/${encodeURIComponent(selected!)}`),
    enabled:Boolean(selected),
    retry:false,
  });

  const archive=useMutation({
    mutationFn:({id,archived}:ArchiveVars)=>api<SavedAnalysis>(`/api/v1/saved-analyses/${encodeURIComponent(id)}?archived=${archived}`,{method:"PATCH"}),
    onSuccess:(item,vars)=>{
      void queryClient.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"saved-analyses")});
      if(workspaceRef.current!==vars.workspaceId)return;
      setNotice(item.archived?"Saved analysis archived.":"Saved analysis restored to the active list.");
      setDeleteConfirm(null);
    },
  });

  const remove=useMutation({
    mutationFn:({id}:RemoveVars)=>api<void>(`/api/v1/saved-analyses/${encodeURIComponent(id)}`,{method:"DELETE"}),
    onSuccess:(_,vars)=>{
      void queryClient.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"saved-analyses")});
      if(workspaceRef.current!==vars.workspaceId)return;
      if(selected===vars.analysisId)setSelected(null);
      setDeleteConfirm(null);
      setNotice("Saved reference deleted. The underlying persisted analysis remains in workspace history.");
    },
  });

  useEffect(()=>{
    workspaceRef.current=workspaceId;
    setIncludeArchived(false);
    setSearch("");
    setSelected(null);
    setDeleteConfirm(null);
    setNotice("");
    archive.reset();
    remove.reset();
  },[workspaceId]);

  const items=q.data?.items??[];
  const filtered=useMemo(()=>{
    const needle=search.trim().toLowerCase();
    if(!needle)return items;
    return items.filter(item=>`${item.title} ${item.analysis_id} ${item.archived?"archived":"active"}`.toLowerCase().includes(needle));
  },[items,search]);

  const actionFailure=archive.error??remove.error;
  const selectedSaved=items.find(item=>item.analysis_id===selected);
  const missing=stringList(detail.data?.missing_data);

  return <>
    <div className="workspaceHeader"><div><h1>Saved Analyses</h1><p>Retain, inspect and manage analysis references inside the active workspace.</p></div><span className="badge">{workspace.name}</span></div>

    <section className="panel" aria-live="polite" data-testid="workspace-saved-state">
      <div className="surfaceToolbar">
        <label className="field"><span>Search</span><input aria-label="Search saved analyses" value={search} onChange={event=>setSearch(event.target.value)} placeholder="Title or analysis reference"/></label>
        <label className="field"><span>Visibility</span><select aria-label="Saved analysis visibility" value={includeArchived?"all":"active"} onChange={event=>setIncludeArchived(event.target.value==="all")}><option value="active">Active only</option><option value="all">Active + archived</option></select></label>
      </div>

      {notice?<p className="success" role="status">{notice}</p>:null}
      {actionFailure?<p className="error" role="alert">{actionError(actionFailure)}</p>:null}
      {q.isPending?<p>Loading saved analyses for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{savedError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>No analyses have been saved in this workspace yet. Save an analysis from an engine result when you want a durable reference here.</p>:null}
      {!q.isPending&&!q.isError&&items.length&&!filtered.length?<p>No saved analyses match the current search and visibility filters.</p>:null}
      {!q.isPending&&!q.isError&&filtered.length?<><p className="sectionLead">Saved references point to canonical persisted analyses. Archiving hides a reference from the default view; deleting a saved reference does not delete the underlying analysis history.</p><div className="tableWrap"><table className="table"><thead><tr><th>Title</th><th>Analysis reference</th><th>Status</th><th>Saved</th><th>Actions</th></tr></thead><tbody>{filtered.map(item=>{
        const busyArchive=archive.isPending&&archive.variables?.id===item.id;
        const busyDelete=remove.isPending&&remove.variables?.id===item.id;
        const isSelected=selected===item.analysis_id;
        return <tr key={item.id}>
          <td>{item.title}</td>
          <td><code>{item.analysis_id}</code></td>
          <td>{item.archived?"Archived":"Active"}</td>
          <td>{savedAt(item.created_at)}</td>
          <td><div className="actions">
            <button className="ghost" onClick={()=>setSelected(current=>current===item.analysis_id?null:item.analysis_id)} aria-expanded={isSelected}>{isSelected?"Hide evidence":"Inspect evidence"}</button>
            <button className="ghost" disabled={busyArchive||busyDelete} onClick={()=>archive.mutate({workspaceId,id:item.id,archived:!item.archived})}>{busyArchive?"Updating…":item.archived?"Restore":"Archive"}</button>
            {deleteConfirm===item.id?<><button className="button" disabled={busyDelete||busyArchive} onClick={()=>remove.mutate({workspaceId,id:item.id,analysisId:item.analysis_id})}>{busyDelete?"Deleting…":"Confirm delete"}</button><button className="ghost" disabled={busyDelete} onClick={()=>setDeleteConfirm(null)}>Cancel</button></>:<button className="ghost" disabled={busyArchive||busyDelete} onClick={()=>setDeleteConfirm(item.id)}>Delete</button>}
          </div></td>
        </tr>;
      })}</tbody></table></div></>:null}
    </section>

    {selected?<section className="panel" aria-live="polite" data-testid="saved-analysis-detail">
      <div className="panelHeading"><div><p className="workspaceKicker">PERSISTED EVIDENCE</p><h2>{selectedSaved?.title??"Saved analysis"}</h2></div><code>{selected}</code></div>
      {detail.isPending?<p>Loading canonical analysis evidence…</p>:null}
      {detail.isError?<p className="error" role="alert">{detailError(detail.error)}</p>:null}
      {detail.data?<><div className="tableWrap"><table className="table"><tbody>
        <tr><th scope="row">Status</th><td>{text(detail.data.status,"UNKNOWN")}</td></tr>
        <tr><th scope="row">Engine</th><td>{text(detail.data.engine_id)}</td></tr>
        <tr><th scope="row">Engine version</th><td>{text(detail.data.engine_version)}</td></tr>
        <tr><th scope="row">Mode</th><td>{detail.data.demo===true?"Demonstration":"Non-demo"}</td></tr>
        <tr><th scope="row">Risk score</th><td>{numberText(detail.data.risk_score,"/100")}</td></tr>
        <tr><th scope="row">Data confidence</th><td>{numberText(detail.data.data_confidence,"%")}</td></tr>
        <tr><th scope="row">Evidence records</th><td>{String(evidenceCount(detail.data.evidence))}</td></tr>
        <tr><th scope="row">Provider consensus</th><td>{text(detail.data.provider_consensus,"UNAVAILABLE")}</td></tr>
      </tbody></table></div>
      {missing.length?<><h3>Missing evidence</h3><ul>{missing.map(item=><li key={item}>{item}</li>)}</ul></>:<p className="muted">No missing-evidence entries are recorded in this persisted result.</p>}</>:null}
    </section>:null}
  </>;
}
