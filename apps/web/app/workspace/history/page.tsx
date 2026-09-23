"use client";

import {useQuery} from "@tanstack/react-query";
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

function historyError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load this workspace history.";
    if(error.status===403||error.status===404)return "History is unavailable because access to this workspace could not be confirmed.";
    if(error.status===503)return "History is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not load history for this workspace.";
}

function recordedAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
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
      {!q.isPending&&!q.isError&&items.length?<><p className="sectionLead">The API returns at most 50 recent records. This table does not imply a lifetime total.</p><div className="tableWrap"><table className="table"><thead><tr><th>Type</th><th>Reference</th><th>Engine</th><th>Mode</th><th>Recorded</th></tr></thead><tbody>{items.map(item=><tr key={`${item.type}-${item.id}`}><td>{item.type}</td><td><code>{item.id}</code></td><td>{item.engine_id??"—"}</td><td>{item.type==="analysis"?(item.demo?"Demo":"Connected/direct"):"—"}</td><td>{recordedAt(item.created_at)}</td></tr>)}</tbody></table></div></>:null}
    </section>
  </>;
}
