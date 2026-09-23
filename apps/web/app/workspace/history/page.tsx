"use client";

import {useQuery} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type HistoryRow={type:"analysis"|"decision";id:string;workspace_id:string;engine_id?:string;demo?:boolean;created_at:string};

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
  const q=useQuery({queryKey:workspaceQueryKey(workspaceId,"history"),queryFn:()=>api<{items:HistoryRow[]}>(`/api/v1/history?workspace_id=${encodeURIComponent(workspaceId)}&limit=100`),retry:false});
  const items=q.data?.items??[];
  const analyses=items.filter(row=>row.type==="analysis").length;
  const decisions=items.filter(row=>row.type==="decision").length;
  return <>
    <div className="workspaceHeader"><div><h1>History</h1><p>Authorized analysis and decision records retained for the active workspace. The view is limited to the most recent 100 records returned by the API.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel" aria-live="polite" data-testid="workspace-history-state">
      {q.isPending?<p>Loading history for {workspace.name}…</p>:null}
      {q.isError?<p className="error" role="alert">{historyError(q.error)}</p>:null}
      {!q.isPending&&!q.isError&&!items.length?<p>No analyses or decisions are recorded in this workspace yet.</p>:null}
      {!q.isPending&&!q.isError&&items.length?<>
        <div style={{display:"flex",gap:18,flexWrap:"wrap",marginBottom:14}}><span><b>{items.length}</b> recent records</span><span><b>{analyses}</b> analyses</span><span><b>{decisions}</b> decisions</span></div>
        <div className="tableWrap"><table className="table"><thead><tr><th>Created</th><th>Record</th><th>Engine</th><th>Analysis mode</th><th>ID</th></tr></thead><tbody>{items.map(row=><tr key={`${row.type}-${row.id}`}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.type}</td><td>{row.engine_id??"—"}</td><td>{row.type==="analysis"?(row.demo?"Demonstration":"Provider/direct-state"):"—"}</td><td><code>{row.id}</code></td></tr>)}</tbody></table></div>
      </>:null}
    </section>
  </>;
}
