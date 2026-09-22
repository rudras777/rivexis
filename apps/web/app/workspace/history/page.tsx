"use client";

import {useQuery} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type HistoryRow=Record<string,string|boolean|number|null|undefined>;

function historyError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load this workspace history.";
    if(error.status===403||error.status===404)return "History is unavailable because access to this workspace could not be confirmed.";
    if(error.status===503)return "History is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load history for this workspace.";
}

export default function History(){
  const {workspaceId,workspace}=useWorkspace();
  const q=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"history"),
    queryFn:()=>api<{items:HistoryRow[]}>(`/api/v1/history?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const items=q.data?.items??[];
  return <>
    <div className="workspaceHeader"><div><h1>History</h1><p>Analyses and decisions retained for the active workspace only.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel" aria-live="polite" data-testid="workspace-history-state">
      {q.isPending?<p>Loading history for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{historyError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>No analyses or decisions are recorded in this workspace yet.</p>:null}
      {!q.isPending&&!q.isError&&items.length?<pre className="result">{JSON.stringify(items,null,2)}</pre>:null}
    </section>
  </>;
}
