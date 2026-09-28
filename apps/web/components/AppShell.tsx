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

const navGroups=[
  {label:"Command",items:[["Overview","/workspace","01"],["Decision Desk","/workspace/decisions","02"]]},
  {label:"Operations",items:[["Protocol History","/workspace/protocol-history","03"],["Investigations","/workspace/investigations","04"],["Monitors","/workspace/monitors","05"],["Alerts","/workspace/alerts","06"]]},
  {label:"Evidence",items:[["History","/workspace/history","07"],["Saved","/workspace/saved","08"]]},
  {label:"Infrastructure",items:[["Providers","/workspace/providers","09"],["Workspaces","/workspace/settings","10"]]},
];

type ShellStateProps={title:string;message:string;kind:"loading"|"empty"|"session"|"unavailable";action?:React.ReactNode};

function ShellState({title,message,kind,action}:ShellStateProps){
  const live=kind==="loading"||kind==="empty"?"status":"alert";
  return <div className="appShell">
    <div className="workspaceAmbient" aria-hidden="true"/>
    <a className="skipLink" href="#workspace-main">Skip to workspace content</a>
    <aside className="sidebar shellStateSidebar"><Brand variant="rail"/><div className="environment">MVP / WORKSPACE-SCOPED</div><div className="sideFoot"><div className="decisionLegend"><b>Decision states</b><span>PROCEED · MODIFY · WAIT · AVOID · UNKNOWN</span></div></div></aside>
    <main className="workspaceMain shellState" id="workspace-main"><section className="shellStateCard" role={live} aria-live="polite" data-testid={`workspace-shell-${kind}`}><div className="shellStateKicker">Workspace access</div><h1>{title}</h1><p>{message}</p>{action?<div className="shellStateActions">{action}</div>:null}</section></main>
  </div>;
}

function clearClientSessionState(){setCsrfToken(null);clearActiveWorkspaceId()}

export function AppShell({children}:{children:React.ReactNode}){
  const p=usePathname();
  const router=useRouter();
  const queryClient=useQueryClient();
  const [active,setActive]=useState("");
  const [loggingOut,setLoggingOut]=useState(false);
  const [logoutError,setLogoutError]=useState("");
  const q=useQuery({queryKey:["workspaces-shell"],queryFn:()=>api<{items:WorkspaceSummary[]}>("/api/v1/workspaces"),retry:false});
  const apiStatus=q.error instanceof ApiError?q.error.status:null;

  function clearWorkspaceQueries(workspaceId?:string|null){
    if(workspaceId){void queryClient.cancelQueries({queryKey:["workspace",workspaceId]});queryClient.removeQueries({queryKey:["workspace",workspaceId]});return}
    void queryClient.cancelQueries({queryKey:["workspace"]});queryClient.removeQueries({queryKey:["workspace"]});
  }

  useEffect(()=>{if(apiStatus!==401)return;clearWorkspaceQueries();clearClientSessionState()},[apiStatus]);

  useEffect(()=>{
    if(!q.data)return;
    if(!q.data.items.length){clearWorkspaceQueries();clearActiveWorkspaceId();setActive("");return}
    const stored=activeWorkspaceId();
    const chosen=q.data.items.find(w=>w.id===stored)?.id??q.data.items[0].id;
    if(stored&&stored!==chosen){clearWorkspaceQueries(stored);window.dispatchEvent(new CustomEvent("rivexis-workspace-change",{detail:{workspaceId:chosen,previousWorkspaceId:stored}}))}
    setActive(chosen);setActiveWorkspaceId(chosen);
  },[q.data]);

  function change(id:string){
    const previous=active||activeWorkspaceId();
    if(previous===id)return;
    if(previous)clearWorkspaceQueries(previous);
    setActive(id);setActiveWorkspaceId(id);setLogoutError("");
    window.dispatchEvent(new CustomEvent("rivexis-workspace-change",{detail:{workspaceId:id,previousWorkspaceId:previous}}));
  }

  async function logout(){
    if(loggingOut)return;setLoggingOut(true);setLogoutError("");
    try{await api("/api/v1/auth/logout",{method:"POST"})}
    catch(error){
      if(!(error instanceof ApiError)||error.status!==401){setLogoutError("Rivexis could not confirm logout. Retry before leaving this device.");setLoggingOut(false);return}
    }
    clearWorkspaceQueries();clearClientSessionState();router.replace("/login");router.refresh();
  }

  if(q.isPending)return <ShellState kind="loading" title="Loading workspace access" message="Rivexis is verifying your session and authorized workspaces before showing workspace navigation."/>;
  if(q.isError){
    if(apiStatus===401)return <ShellState kind="session" title="Session ended" message="Your Rivexis session is missing, expired, or revoked. Workspace data has not been shown." action={<><Link className="button" href="/login">Log in again</Link><Link className="ghost" href="/">Public site</Link></>}/>;
    if(apiStatus===403)return <ShellState kind="unavailable" title="Workspace access unavailable" message="Your account is authenticated, but Rivexis could not confirm authorization for this workspace area. No workspace data has been shown." action={<><button className="button" type="button" onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?"Retrying…":"Retry access check"}</button><Link className="ghost" href="/">Public site</Link></>}/>;
    return <ShellState kind="unavailable" title={apiStatus===503?"Application services unavailable":"Workspace could not load"} message={apiStatus===503?"The application API is currently unavailable, so Rivexis has withheld authenticated navigation and workspace content.":"Rivexis could not verify workspace access. No authenticated workspace data has been shown."} action={<><button className="button" type="button" onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?"Retrying…":"Retry"}</button><Link className="ghost" href="/">Public site</Link></>}/>;
  }
  if(!q.data.items.length)return <ShellState kind="empty" title="No workspace configured" message="Your session is valid, but there is no authorized workspace to enter yet. Configure a workspace before using Rivexis analysis or monitoring tools." action={<><Link className="button" href="/onboarding">Configure workspace</Link><Link className="ghost" href="/">Public site</Link></>}/>;

  const selected=active||q.data.items[0].id;
  const selectedWorkspace=q.data.items.find(w=>w.id===selected)??q.data.items[0];
  const contextValue={workspaceId:selected,workspace:selectedWorkspace,workspaces:q.data.items,switchWorkspace:change};

  return <div className="appShell">
    <div className="workspaceAmbient" aria-hidden="true"/>
    <a className="skipLink" href="#workspace-main">Skip to workspace content</a>
    <aside className="sidebar"><Brand variant="rail"/><div className="environment"><span className="statusDot"/>PRODUCTION WORKSPACE</div><label className="workspaceSelector">ACTIVE WORKSPACE<select value={selected} onChange={e=>change(e.target.value)}>{q.data.items.map(w=><option key={w.id} value={w.id}>{w.name} · {w.access_role}</option>)}</select></label><nav aria-label="Workspace">{navGroups.map(group=><div className="navGroup" key={group.label}><span className="navGroupLabel">{group.label}</span>{group.items.map(([n,h,number])=>{const current=p===h;return <Link key={h} href={h} className={current?"active":""} aria-current={current?"page":undefined}><span className="navIndex">{number}</span><span>{n}</span></Link>})}</div>)}</nav><div className="sideFoot"><button type="button" className="sidebarLogout" aria-label={loggingOut?"Logging out…":"Log out"} onClick={logout} disabled={loggingOut}>{loggingOut?"Logging out…":"Log out securely"}<span aria-hidden="true">↗</span></button>{logoutError?<div className="sidebarError" role="alert">{logoutError}</div>:null}<div className="decisionLegend"><b>Decision policy</b><span>PROCEED · MODIFY · WAIT · AVOID · UNKNOWN</span></div></div></aside>
    <main className="workspaceMain" id="workspace-main"><WorkspaceContextProvider value={contextValue}>{children}</WorkspaceContextProvider></main>
  </div>;
}
