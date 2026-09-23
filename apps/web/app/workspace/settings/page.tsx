"use client";

import {useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

type Workspace={id:string;name:string;role:string;organization_id?:string|null;access_role:string;created_at?:string};
type Org={id:string;name:string;member_role:string;created_at:string};

function listError(error:unknown,kind:"workspaces"|"organizations"){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load these settings.";
    if(error.status===403)return kind==="organizations"?"Organization access could not be confirmed for this account.":"Workspace access could not be confirmed for this account.";
    if(error.status===503)return "Settings are temporarily unavailable because the application API is unavailable.";
  }
  return kind==="organizations"?"Rivexis could not load organizations for this account.":"Rivexis could not load your authorized workspaces.";
}

function createdAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}

export default function Settings(){
  const qc=useQueryClient();
  const {workspaceId,switchWorkspace}=useWorkspace();
  const [name,setName]=useState("Institutional Workspace");
  const [role,setRole]=useState("Analyst");
  const [orgName,setOrgName]=useState("Rivexis Organization");
  const ws=useQuery({queryKey:["workspace-settings"],queryFn:()=>api<{items:Workspace[]}>("/api/v1/workspaces"),retry:false});
  const orgs=useQuery({queryKey:["organizations"],queryFn:()=>api<{items:Org[]}>("/api/v1/organizations"),retry:false});
  const makeWs=useMutation({
    mutationFn:()=>api<Workspace>("/api/v1/workspaces",{method:"POST",body:JSON.stringify({name:name.trim(),role})}),
    onSuccess:r=>{
      qc.setQueryData<{items:Workspace[]}>(["workspace-settings"],old=>({items:[...(old?.items??[]).filter(w=>w.id!==r.id),r]}));
      qc.setQueryData<{items:Workspace[]}>(["workspaces-shell"],old=>({items:[...(old?.items??[]).filter(w=>w.id!==r.id),r]}));
      switchWorkspace(r.id);
      void qc.invalidateQueries({queryKey:["workspace-settings"]});
      void qc.invalidateQueries({queryKey:["workspaces-shell"]});
    }
  });
  const makeOrg=useMutation({
    mutationFn:()=>api<Org>("/api/v1/organizations",{method:"POST",body:JSON.stringify({name:orgName.trim()})}),
    onSuccess:r=>{
      qc.setQueryData<{items:Org[]}>(["organizations"],old=>({items:[r,...(old?.items??[]).filter(org=>org.id!==r.id)]}));
      void qc.invalidateQueries({queryKey:["organizations"]});
    }
  });

  return <>
    <div className="workspaceHeader"><div><h1>Workspaces & Organizations</h1><p>This surface lists only workspaces and organizations returned for the authenticated account. It does not imply broader administration access.</p></div><span className="badge">ACTIVE {workspaceId}</span></div>
    <section className="panel"><h2>Your workspaces</h2>
      {ws.isPending?<p>Loading authorized workspaces…</p>:null}
      {ws.isError?<p className="error" role="alert">{listError(ws.error,"workspaces")}</p>:null}
      {!ws.isPending&&!ws.isError&&!ws.data?.items.length?<p>No workspaces are currently authorized for this account.</p>:null}
      {!ws.isPending&&!ws.isError&&ws.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Context</th><th>Access</th><th>Organization</th><th>Action</th></tr></thead><tbody>{ws.data.items.map(w=><tr key={w.id}><td>{w.name}</td><td>{w.role}</td><td>{w.access_role}</td><td>{w.organization_id??"Personal"}</td><td><button className="button" type="button" disabled={w.id===workspaceId} onClick={()=>switchWorkspace(w.id)}>{w.id===workspaceId?"Active":"Use"}</button></td></tr>)}</tbody></table></div>:null}
    </section>
    <section className="panel"><h2>Create personal workspace</h2><p className="sectionLead">A personal workspace is owned by the current account. This form does not create organization membership or grant access to other users.</p><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Name<input value={name} onChange={e=>setName(e.target.value)}/></label><label className="field">Context<select value={role} onChange={e=>setRole(e.target.value)}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label><button className="button" type="button" disabled={makeWs.isPending||name.trim().length<2} onClick={()=>makeWs.mutate()}>{makeWs.isPending?"Creating…":"Create"}</button></div>{makeWs.isSuccess?<p role="status">Created <b>{makeWs.data.name}</b> and made it the active workspace.</p>:null}{makeWs.isError?<p className="error" role="alert">Rivexis could not create the workspace. Review the input and retry.</p>:null}</section>
    <section className="panel"><h2>Organizations</h2><p className="sectionLead">The role shown here is your membership role in each organization. Member administration is not exposed on this page.</p>{orgs.isPending?<p>Loading organizations…</p>:null}{orgs.isError?<p className="error" role="alert">{listError(orgs.error,"organizations")}</p>:null}{!orgs.isPending&&!orgs.isError&&!orgs.data?.items.length?<p>No organizations are currently associated with this account.</p>:null}{!orgs.isPending&&!orgs.isError&&orgs.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Your role</th><th>Created</th></tr></thead><tbody>{orgs.data.items.map(org=><tr key={org.id}><td>{org.name}</td><td>{org.member_role}</td><td>{createdAt(org.created_at)}</td></tr>)}</tbody></table></div>:null}<div style={{display:"flex",gap:12,marginTop:16,alignItems:"end"}}><label className="field" style={{flex:1}}>Organization name<input value={orgName} onChange={e=>setOrgName(e.target.value)}/></label><button className="button" type="button" disabled={makeOrg.isPending||orgName.trim().length<2} onClick={()=>makeOrg.mutate()}>{makeOrg.isPending?"Creating…":"Create organization"}</button></div>{makeOrg.isSuccess?<p role="status">Created <b>{makeOrg.data.name}</b>. Your membership role is {makeOrg.data.member_role}.</p>:null}{makeOrg.isError?<p className="error" role="alert">Rivexis could not create the organization. Review the input and retry.</p>:null}</section>
  </>;
}
