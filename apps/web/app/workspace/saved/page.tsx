"use client";

import {useQuery} from "@tanstack/react-query";
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

function savedError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load saved analyses.";
    if(error.status===403||error.status===404)return "Saved analyses are unavailable because access to this workspace could not be confirmed.";
    if(error.status===503)return "Saved analyses are temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load saved analyses for this workspace.";
}

function savedAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}

export default function Saved(){
  const {workspaceId,workspace}=useWorkspace();
  const q=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"saved-analyses"),
    queryFn:()=>api<{items:SavedAnalysis[]}>(`/api/v1/saved-analyses?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const items=q.data?.items??[];
  return <>
    <div className="workspaceHeader"><div><h1>Saved Analyses</h1><p>Authenticated analysis references retained for the active workspace only.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel" aria-live="polite" data-testid="workspace-saved-state">
      {q.isPending?<p>Loading saved analyses for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{savedError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>No analyses have been saved in this workspace yet.</p>:null}
      {!q.isPending&&!q.isError&&items.length?<><p className="sectionLead">Only active saved references are returned by this view; archived references are excluded by the API default.</p><div className="tableWrap"><table className="table"><thead><tr><th>Title</th><th>Analysis reference</th><th>Status</th><th>Saved</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{item.title}</td><td><code>{item.analysis_id}</code></td><td>{item.archived?"Archived":"Active"}</td><td>{savedAt(item.created_at)}</td></tr>)}</tbody></table></div></>:null}
    </section>
  </>;
}
