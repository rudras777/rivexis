"use client";

import Link from "next/link";
import {usePathname,useRouter} from "next/navigation";
import {useQuery,useQueryClient} from "@tanstack/react-query";
import {useEffect,useState} from "react";
import {Brand} from "./Brand";
import {WorkspaceContextProvider,type WorkspaceSummary} from "./WorkspaceContext";
import {
  ApiError,
  activeWorkspaceId,
  api,
  clearActiveWorkspaceId,
  setActiveWorkspaceId,
  setCsrfToken,
} from "@/lib/api";

const nav=[
  ["Overview","/workspace"],
  ["Workspaces","/workspace/settings"],
  ["Providers","/workspace/providers"],
  ["Protocol History","/workspace/protocol-history"],
  ["Investigations","/workspace/investigations"],
  ["Monitors","/workspace/monitors"],
  ["History","/workspace/history"],
  ["Saved","/workspace/saved"],
];

type ShellStateProps={
  title:string;
  message:string;
  kind:"loading"|"empty"|"session"|"unavailable";
  action?:React.ReactNode;
};

function ShellState({title,message,kind,action}:ShellStateProps){
  const live=kind==="loading"||kind==="empty"?"status":"alert";
  return <div className="appShell">
    <a className="skipLink" href="#workspace-main">Skip to workspace content</a>
    <aside className="sidebar shellStateSidebar">
      <Brand/>
      <div className="environment">MVP / WORKSPACE-SCOPED</div>
      <div className="sideFoot">
        <div className="decisionLegend">
          <b>Decision states</b>
          <span>PROCEED · MODIFY · WAIT · AVOID · UNKNOWN</span>
        </div>
      </div>
    </aside>
    <main className="workspaceMain shellState" id="workspace-main">
      <section className="shellStateCard" role={live} aria-live="polite" data-testid={`workspace-shell-${kind}`}>
        <div className="shellStateKicker">Workspace access</div>
        <h1>{title}</h1>
        <p>{message}</p>
        {action?<div className="shellStateActions">{action}</div>:null}
      </section>
    </main>
  </div>;
}

function clearClientSessionState(){
  setCsrfToken(null);
  clearActiveWorkspaceId();
}

export function AppShell({children}:{children:React.ReactNode}){
  const p=usePathname();
  const router=useRouter();
  const queryClient=useQueryClient();
  const [active,setActive]=useState("");
  const [loggingOut,setLoggingOut]=useState(false);
  const [logoutError,setLogoutError]=useState("");
  const q=useQuery({
    queryKey:["workspaces-shell"],
    queryFn:()=>api<{items:WorkspaceSummary[]}>("/api/v1/workspaces"),
    retry:false,
  });

  const apiStatus=q.error instanceof ApiError?q.error.status:null;

  function clearWorkspaceQueries(workspaceId?:string|null){
    if(workspaceId){
      void queryClient.cancelQueries({queryKey:["workspace",workspaceId]});
      queryClient.removeQueries({queryKey:["workspace",workspaceId]});
      return;
    }
    void queryClient.cancelQueries({queryKey:["workspace"]});
    queryClient.removeQueries({queryKey:["workspace"]});
  }

  useEffect(()=>{
    if(apiStatus!==401)return;
    clearWorkspaceQueries();
    clearClientSessionState();
  },[apiStatus]);

  useEffect(()=>{
    if(!q.data)return;
    if(!q.data.items.length){
      clearWorkspaceQueries();
      clearActiveWorkspaceId();
      setActive("");
      return;
    }
    const stored=activeWorkspaceId();
    const chosen=q.data.items.find(w=>w.id===stored)?.id??q.data.items[0].id;
    if(stored&&stored!==chosen){
      clearWorkspaceQueries(stored);
      window.dispatchEvent(new CustomEvent("rivexis-workspace-change",{detail:{workspaceId:chosen,previousWorkspaceId:stored}}));
    }
    setActive(chosen);
    setActiveWorkspaceId(chosen);
  },[q.data]);

  function change(id:string){
    const previous=active||activeWorkspaceId();
    if(previous===id)return;
    if(previous)clearWorkspaceQueries(previous);
    setActive(id);
    setActiveWorkspaceId(id);
    setLogoutError("");
    window.dispatchEvent(new CustomEvent("rivexis-workspace-change",{detail:{workspaceId:id,previousWorkspaceId:previous}}));
    // Several legacy tool pages still hold workspace-local results in component state.
    // Keep a hard navigation boundary until each of those pages is migrated to keyed
    // workspace state; this prevents a selected result from one workspace surviving
    // visually after a switch.
    window.location.reload();
  }

  async function logout(){
    if(loggingOut)return;
    setLoggingOut(true);
    setLogoutError("");
    try{
      await api("/api/v1/auth/logout",{method:"POST"});
    }catch(error){
      if(!(error instanceof ApiError)||error.status!==401){
        setLogoutError("Rivexis could not confirm logout. Retry before leaving this device.");
        setLoggingOut(false);
        return;
      }
      // A 401 during CSRF bootstrap or logout means the server session is already
      // missing/revoked. Finish local cleanup and route to the unauthenticated surface.
    }
    clearWorkspaceQueries();
    clearClientSessionState();
    router.replace("/login");
    router.refresh();
  }

  if(q.isPending){
    return <ShellState
      kind="loading"
      title="Loading workspace access"
      message="Rivexis is verifying your session and authorized workspaces before showing workspace navigation."
    />;
  }

  if(q.isError){
    if(apiStatus===401){
      return <ShellState
        kind="session"
        title="Session ended"
        message="Your Rivexis session is missing, expired, or revoked. Workspace data has not been shown."
        action={<><Link className="button" href="/login">Log in again</Link><Link className="ghost" href="/">Public site</Link></>}
      />;
    }

    if(apiStatus===403){
      return <ShellState
        kind="unavailable"
        title="Workspace access unavailable"
        message="Your account is authenticated, but Rivexis could not confirm authorization for this workspace area. No workspace data has been shown."
        action={<><button className="button" type="button" onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?"Retrying…":"Retry access check"}</button><Link className="ghost" href="/">Public site</Link></>}
      />;
    }

    return <ShellState
      kind="unavailable"
      title={apiStatus===503?"Application services unavailable":"Workspace could not load"}
      message={apiStatus===503
        ?"The application API is currently unavailable, so Rivexis has withheld authenticated navigation and workspace content."
        :"Rivexis could not verify workspace access. No authenticated workspace data has been shown."}
      action={<><button className="button" type="button" onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?"Retrying…":"Retry"}</button><Link className="ghost" href="/">Public site</Link></>}
    />;
  }

  if(!q.data.items.length){
    return <ShellState
      kind="empty"
      title="No workspace configured"
      message="Your session is valid, but there is no authorized workspace to enter yet. Configure a workspace before using Rivexis analysis or monitoring tools."
      action={<><Link className="button" href="/onboarding">Configure workspace</Link><Link className="ghost" href="/">Public site</Link></>}
    />;
  }

  const selected=active||q.data.items[0].id;
  const selectedWorkspace=q.data.items.find(w=>w.id===selected)??q.data.items[0];
  const contextValue={workspaceId:selected,workspace:selectedWorkspace,workspaces:q.data.items,switchWorkspace:change};

  return <div className="appShell">
    <a className="skipLink" href="#workspace-main">Skip to workspace content</a>
    <aside className="sidebar">
      <Brand/>
      <div className="environment">MVP / WORKSPACE-SCOPED</div>
      <label className="workspaceSelector">
        ACTIVE WORKSPACE
        <select value={selected} onChange={e=>change(e.target.value)}>
          {q.data.items.map(w=><option key={w.id} value={w.id}>{w.name} · {w.access_role}</option>)}
        </select>
      </label>
      <nav aria-label="Workspace">
        {nav.map(([n,h])=>{
          const current=p===h;
          return <Link key={h} href={h} className={current?"active":""} aria-current={current?"page":undefined}>{n}</Link>;
        })}
      </nav>
      <div className="sideFoot">
        <button type="button" className="ghost" onClick={logout} disabled={loggingOut}>{loggingOut?"Logging out…":"Log out"}</button>
        {logoutError?<div className="sidebarError" role="alert">{logoutError}</div>:null}
        <div className="decisionLegend">
          <b>Decision states</b>
          <span>PROCEED · MODIFY · WAIT · AVOID · UNKNOWN</span>
        </div>
      </div>
    </aside>
    <main className="workspaceMain" id="workspace-main">
      <WorkspaceContextProvider value={contextValue}>{children}</WorkspaceContextProvider>
    </main>
  </div>;
}
