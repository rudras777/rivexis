"use client";

import {useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {api} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

type Workspace={id:string;name:string;role:string;organization_id?:string|null;access_role:string};
type Org={id:string;name:string;member_role:string};

export default function Settings(){
  const qc=useQueryClient();
  const {workspaceId,switchWorkspace}=useWorkspace();
  const [name,setName]=useState("Institutional Workspace");
  const [role,setRole]=useState("Analyst");
  const [orgName,setOrgName]=useState("Rivexis Organization");
  const ws=useQuery({queryKey:["workspace-settings"],queryFn:()=>api<{items:Workspace[]}>("/api/v1/workspaces"),retry:false});
  const orgs=useQuery({queryKey:["organizations"],queryFn:()=>api<{items:Org[]}>("/api/v1/organizations"),retry:false});
  const makeWs=useMutation({
    mutationFn:()=>api<Workspace>("/api/v1/workspaces",{method:"POST",body:JSON.stringify({name,role})}),
    onSuccess:r=>{
      qc.setQueryData<{items:Workspace[]}>(["workspace-settings"],old=>({items:[...(old?.items??[]).filter(w=>w.id!==r.id),r]}));
      qc.setQueryData<{items:Workspace[]}>(["workspaces-shell"],old=>({items:[...(old?.items??[]).filter(w=>w.id!==r.id),r]}));
      switchWorkspace(r.id);
      void qc.invalidateQueries({queryKey:["workspace-settings"]});
      void qc.invalidateQueries({queryKey:["workspaces-shell"]});
    }
  });
  const makeOrg=useMutation({
    mutationFn:()=>api<Org>("/api/v1/organizations",{method:"POST",body:JSON.stringify({name:orgName})}),
    onSuccess:()=>void qc.invalidateQueries({queryKey:["organizations"]})
  });

  return <>
    <div className="workspaceHeader"><div><h1>Workspaces & Organizations</h1><p>Access is enforced by the API. Organization roles are OWNER, ADMIN, ANALYST and VIEWER.</p></div><span className="badge">ACTIVE {workspaceId}</span></div>
    <section className="panel"><h2>Your workspaces</h2>
      {ws.isPending?<p>Loading authorized workspaces…</p>:null}
      {ws.isError?<p className="error" role="alert">Rivexis could not load your authorized workspaces.</p>:null}
      {!ws.isPending&&!ws.isError&&!ws.data?.items.length?<p>No workspaces are currently authorized for this account.</p>:null}
      {!ws.isPending&&!ws.isError&&ws.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Context</th><th>Access</th><th>Organization</th><th></th></tr></thead><tbody>{ws.data.items.map(w=><tr key={w.id}><td>{w.name}</td><td>{w.role}</td><td>{w.access_role}</td><td>{w.organization_id??"Personal"}</td><td><button className="button" disabled={w.id===workspaceId} onClick={()=>switchWorkspace(w.id)}>{w.id===workspaceId?"Active":"Use"}</button></td></tr>)}</tbody></table></div>:null}
    </section>
    <section className="panel"><h2>Create personal workspace</h2><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Name<input value={name} onChange={e=>setName(e.target.value)}/></label><label className="field">Role<select value={role} onChange={e=>setRole(e.target.value)}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label><button className="button" disabled={makeWs.isPending||name.trim().length<2} onClick={()=>makeWs.mutate()}>{makeWs.isPending?"Creating…":"Create"}</button></div>{makeWs.isError?<p className="error" role="alert">Rivexis could not create the workspace. Review the input and retry.</p>:null}</section>
    <section className="panel"><h2>Organizations</h2>{orgs.isPending?<p>Loading organizations…</p>:null}{orgs.isError?<p className="error" role="alert">Rivexis could not load organizations for this account.</p>:null}{!orgs.isPending&&!orgs.isError?<pre className="result">{JSON.stringify(orgs.data?.items??[],null,2)}</pre>:null}<div style={{display:"flex",gap:12,marginTop:12}}><input value={orgName} onChange={e=>setOrgName(e.target.value)} style={{flex:1}}/><button className="button" disabled={makeOrg.isPending||orgName.trim().length<2} onClick={()=>makeOrg.mutate()}>{makeOrg.isPending?"Creating…":"Create organization"}</button></div>{makeOrg.isError?<p className="error" role="alert">Rivexis could not create the organization. Review the input and retry.</p>:null}</section>
  </>;
}
