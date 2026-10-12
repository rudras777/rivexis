"use client";

import Link from "next/link";
import {usePathname,useRouter} from "next/navigation";
import {useQuery,useQueryClient} from "@tanstack/react-query";
import {useEffect,useState,useRef} from "react";
import {authHref,safeDestination} from "@/lib/auth-destination";
import {useDeFi} from "./DeFiContext";
import {WorkspaceNavigation} from "./WorkspaceNavigation";
import {useWalletConnection} from "./WalletConnection";
import {Brand} from "./Brand";
import {useAccountPreferences} from "./AccountPreferences";
import {WorkspaceContextProvider,type WorkspaceSummary} from "./WorkspaceContext";
import {
  ApiError,
  activeWorkspaceId,
  api,
  clearActiveWorkspaceId,
  setActiveWorkspaceId,
  setCsrfToken,
} from "@/lib/api";


type ShellStateProps={title:string;message:string;kind:"loading"|"empty"|"session"|"unavailable";action?:React.ReactNode};

function ShellState({title,message,kind,action}:ShellStateProps){
  const live=kind==="loading"||kind==="empty"?"status":"alert";
  return <div className="appShell">
    <a className="skipLink" href="#workspace-main">Skip to workspace content</a>
    <header className="workspaceHeaderBar shellAccessHeader"><Brand/><Link className="textButton" href="/methodology">Methodology</Link></header>
    <main className="workspaceMain shellState" id="workspace-main"><section className="shellStateCard" role={live} aria-live="polite" data-testid={`workspace-shell-${kind}`}><div className="shellStateKicker">Workspace access</div><h1>{title}</h1><p>{message}</p>{action?<div className="shellStateActions">{action}</div>:null}</section></main>
  </div>;
}

function clearClientSessionState(){setCsrfToken(null);clearActiveWorkspaceId()}

export function AppShell({children}:{children:React.ReactNode}){
  const p=usePathname(),wallet=useWalletConnection();
  const {account}=useAccountPreferences();
  const accountMenu=useRef<HTMLDetailsElement>(null),mobileMenu=useRef<HTMLDetailsElement>(null);
  useEffect(()=>{if(accountMenu.current)accountMenu.current.open=false;if(mobileMenu.current)mobileMenu.current.open=false},[p]);
  useEffect(()=>{const close=(e:PointerEvent)=>{for(const ref of [accountMenu,mobileMenu])if(ref.current&&!ref.current.contains(e.target as Node))ref.current.open=false};const escape=(e:KeyboardEvent)=>{if(e.key==='Escape')for(const ref of [accountMenu,mobileMenu])if(ref.current?.open){ref.current.open=false;ref.current.querySelector('summary')?.focus()}};document.addEventListener('pointerdown',close);document.addEventListener('keydown',escape);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',escape)}},[]);
  const risk=useDeFi();
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

  useEffect(()=>{if(apiStatus!==401)return;clearWorkspaceQueries();clearClientSessionState();void queryClient.cancelQueries({queryKey:["account-settings"]});queryClient.removeQueries({queryKey:["account-settings"]});risk.reset();window.dispatchEvent(new Event("rivexis-wallet-forget"))},[apiStatus,risk.reset]);

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
    clearWorkspaceQueries();clearClientSessionState();void queryClient.cancelQueries({queryKey:["account-settings"]});queryClient.removeQueries({queryKey:["account-settings"]});risk.reset();window.dispatchEvent(new Event("rivexis-wallet-forget"));queryClient.removeQueries({queryKey:["public-session"]});sessionStorage.removeItem("rivexis_pending_destination");router.replace("/login");router.refresh();
  }

  useEffect(()=>{const request=()=>{void logout()};window.addEventListener("rivexis-request-logout",request);return()=>window.removeEventListener("rivexis-request-logout",request)},[loggingOut]);

  if(q.isPending)return <ShellState kind="loading" title="Loading workspace access" message="Rivexis is verifying your session and authorized workspaces before showing workspace navigation."/>;
  if(q.isError){
    if(apiStatus===401)return <ShellState kind="session" title="Session ended" message="Your Rivexis session is missing, expired, or revoked. Workspace data has not been shown." action={<><Link className="button" href={authHref("/login",safeDestination(p))}>Log in again</Link><Link className="ghost" href="/">Public site</Link></>}/>;
    if(apiStatus===403&&q.error instanceof ApiError&&q.error.message.includes("Email verification"))return <ShellState kind="unavailable" title="Verify your email" message="Your account needs email verification before any platform feature can open." action={<><Link className="button" href={authHref("/verify-email",safeDestination(p))}>Verify email</Link><Link className="ghost" href="/">Public site</Link></>}/>;
    if(apiStatus===403)return <ShellState kind="unavailable" title="Workspace access unavailable" message="Your account is authenticated, but Rivexis could not confirm authorization for this workspace area. No workspace data has been shown." action={<><button className="button" type="button" onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?"Retrying…":"Retry access check"}</button><Link className="ghost" href="/">Public site</Link></>}/>;
    return <ShellState kind="unavailable" title={apiStatus===503?"Application services unavailable":"Workspace could not load"} message={apiStatus===503?"The application API is currently unavailable, so Rivexis has withheld authenticated navigation and workspace content.":"Rivexis could not verify workspace access. No authenticated workspace data has been shown."} action={<><button className="button" type="button" onClick={()=>void q.refetch()} disabled={q.isFetching}>{q.isFetching?"Retrying…":"Retry"}</button><Link className="ghost" href="/">Public site</Link></>}/>;
  }
  if(!q.data.items.length)return <ShellState kind="empty" title="No workspace configured" message="Your session is valid, but there is no authorized workspace to enter yet. Configure a workspace before using Rivexis analysis or monitoring tools." action={<><Link className="button" href={authHref("/onboarding",safeDestination(p))}>Configure workspace</Link><Link className="ghost" href="/">Public site</Link></>}/>;

  const selected=active||q.data.items[0].id;
  const selectedWorkspace=q.data.items.find(w=>w.id===selected)??q.data.items[0];
  const contextValue={workspaceId:selected,workspace:selectedWorkspace,workspaces:q.data.items,switchWorkspace:change};

  return <div className="appShell">
    <a className="skipLink" href="#workspace-main">Skip to workspace content</a>
    <header className="workspaceHeaderBar">
      <Brand/>
      <WorkspaceNavigation/>
      <div className="workspaceHeaderActions"><Link className="walletHeaderControl ghost" href="/workspace/wallets">{wallet.connection?`${wallet.connection.address.slice(0,6)}…${wallet.connection.address.slice(-4)}`:"Connect Wallet"}</Link>
        <details className="workspaceMobileNav" ref={mobileMenu}><summary aria-label="Open workspace navigation">Menu <span aria-hidden="true">⌄</span></summary><WorkspaceNavigation mobile/></details>
        <details className="accountMenu" ref={accountMenu}><summary aria-label="Account menu"><span className="accountInitials" aria-hidden="true">{(account?.profile.displayName||"R").split(/\s+/).slice(0,2).map(n=>n[0]).join("").toUpperCase()}</span><span>Account</span><span aria-hidden="true">⌄</span></summary><nav aria-label="Account"><strong>{account?.profile.displayName||"Your account"}</strong><Link href="/workspace/settings">Settings</Link><Link href="/workspace/settings/workspaces">Workspaces & organizations</Link><Link href="/workspace/history">Historical records</Link><button type="button" className="criticalButton" aria-label={loggingOut?"Logging out…":"Log out"} onClick={logout} disabled={loggingOut}>{loggingOut?"Logging out…":"Log out"}</button></nav></details>
      </div>
    </header>
    <div className="workspaceScope"><label className="workspaceSelector">ACTIVE WORKSPACE<select value={selected} onChange={e=>change(e.target.value)}>{q.data.items.map(w=><option key={w.id} value={w.id}>{w.name} · {w.access_role}</option>)}</select></label><span>Risk · Value · Execution · Analysis</span></div>
    {logoutError?<div className="shellLogoutError error" role="alert">{logoutError}</div>:null}
    <main className="workspaceMain" id="workspace-main"><WorkspaceContextProvider value={contextValue}>{children}</WorkspaceContextProvider></main>
  </div>;
}
