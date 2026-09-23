"use client";

import {useEffect,useRef,useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type SavedItem={id:string;workspace_id:string;analysis_id:string;title:string;archived:boolean;created_at:string};
type ArchiveVars={workspaceId:string;id:string;archived:boolean};

function savedError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load saved analyses.";
    if(error.status===403||error.status===404)return "Saved analyses are unavailable because access to this workspace could not be confirmed.";
    if(error.status===503)return "Saved analyses are temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load saved analyses for this workspace.";
}

export default function Saved(){
  const qc=useQueryClient();
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const [includeArchived,setIncludeArchived]=useState(false);
  const q=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"saved-analyses",includeArchived),
    queryFn:()=>api<{items:SavedItem[]}>(`/api/v1/saved-analyses?workspace_id=${encodeURIComponent(workspaceId)}&include_archived=${includeArchived}`),
    retry:false,
  });
  const archive=useMutation({
    mutationFn:(vars:ArchiveVars)=>api<SavedItem>(`/api/v1/saved-analyses/${vars.id}?archived=${vars.archived}`,{method:"PATCH"}),
    onSuccess:(_row,vars)=>{
      void qc.invalidateQueries({queryKey:["workspace",vars.workspaceId,"saved-analyses"]});
      void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"dashboard-saved")});
    },
  });
  useEffect(()=>{workspaceRef.current=workspaceId;archive.reset()},[workspaceId]);
  const items=q.data?.items??[];
  return <>
    <div className="workspaceHeader"><div><h1>Saved Analyses</h1><p>Personal saved-analysis references within the active authorized workspace. Archiving is reversible and does not delete the underlying analysis record.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel" aria-live="polite" data-testid="workspace-saved-state">
      <label style={{display:"flex",gap:8,alignItems:"center",marginBottom:14}}><input type="checkbox" checked={includeArchived} onChange={e=>setIncludeArchived(e.target.checked)}/> Include archived references</label>
      {q.isPending?<p>Loading saved analyses for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{savedError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>{includeArchived?"No saved analysis references exist in this workspace.":"No active saved analyses exist in this workspace yet."}</p>:null}
      {!q.isPending&&!q.isError&&items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Saved</th><th>Title</th><th>Analysis ID</th><th>State</th><th></th></tr></thead><tbody>{items.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.title||"Untitled analysis"}</td><td><code>{row.analysis_id}</code></td><td>{row.archived?"Archived":"Active"}</td><td><button className="ghost" disabled={archive.isPending&&archive.variables?.id===row.id} onClick={()=>archive.mutate({workspaceId,id:row.id,archived:!row.archived})}>{archive.isPending&&archive.variables?.id===row.id?"Updating…":row.archived?"Restore":"Archive"}</button></td></tr>)}</tbody></table></div>:null}
      {archive.isError&&workspaceRef.current===workspaceId?<p className="error" role="alert">Rivexis could not update that saved-analysis reference. Retry after confirming your session and workspace access.</p>:null}
    </section>
  </>;
}
