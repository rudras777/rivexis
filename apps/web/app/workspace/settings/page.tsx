"use client";

import {useEffect,useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {api} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type Workspace={id:string;name:string;role:string;organization_id?:string|null;access_role:string;created_at?:string};
type Org={id:string;name:string;member_role:string;created_at?:string};
type AuditRow={id:string;actor?:string|null;action:string;resource_type:string;resource_id?:string|null;created_at:string};
type UpdateVars={workspaceId:string;name:string;role:string};

export default function Settings(){
  const qc=useQueryClient();
  const {workspaceId,workspace,workspaces,switchWorkspace}=useWorkspace();
  const [name,setName]=useState("Institutional Workspace");
  const [role,setRole]=useState("Analyst");
  const [orgName,setOrgName]=useState("Rivexis Organization");
  const [editName,setEditName]=useState(workspace.name);
  const [editRole,setEditRole]=useState(workspace.role);
  const canManage=workspace.access_role==="OWNER"||workspace.access_role==="ADMIN";

  useEffect(()=>{setEditName(workspace.name);setEditRole(workspace.role)},[workspaceId,workspace.name,workspace.role]);

  const orgs=useQuery({queryKey:["organizations"],queryFn:()=>api<{items:Org[]}>("/api/v1/organizations"),retry:false});
  const audit=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"audit-logs"),
    queryFn:()=>api<{items:AuditRow[]}>(`/api/v1/workspaces/${workspaceId}/audit-logs?limit=20`),
    enabled:canManage,
    retry:false,
  });
  const makeWs=useMutation({
    mutationFn:()=>api<Workspace>("/api/v1/workspaces",{method:"POST",body:JSON.stringify({name,role})}),
    onSuccess:r=>{
      qc.setQueryData<{items:Workspace[]}>(["workspaces-shell"],old=>({items:[r,...(old?.items??[]).filter(w=>w.id!==r.id)]}));
      switchWorkspace(r.id);
      void qc.invalidateQueries({queryKey:["workspaces-shell"]});
    }
  });
  const updateWs=useMutation({
    mutationFn:(vars:UpdateVars)=>api<Workspace>(`/api/v1/workspaces/${vars.workspaceId}`,{method:"PATCH",body:JSON.stringify({name:vars.name,role:vars.role})}),
    onSuccess:(row,vars)=>{
      qc.setQueryData<{items:Workspace[]}>(["workspaces-shell"],old=>({items:(old?.items??[]).map(w=>w.id===row.id?{...w,...row}:w)}));
      void qc.invalidateQueries({queryKey:["workspaces-shell"]});
      void qc.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"audit-logs")});
    },
  });
  const makeOrg=useMutation({mutationFn:()=>api<Org>("/api/v1/organizations",{method:"POST",body:JSON.stringify({name:orgName})}),onSuccess:()=>void qc.invalidateQueries({queryKey:["organizations"]})});

  return <>
    <div className="workspaceHeader"><div><h1>Workspaces & Organizations</h1><p>Workspace context and management permissions are enforced by the API. Organization member administration remains outside this Milestone D surface.</p></div><span className="badge">{workspace.name} · {workspace.access_role}</span></div>

    <section className="panel"><h2>Your authorized workspaces</h2><div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Context</th><th>Access</th><th>Organization</th><th></th></tr></thead><tbody>{workspaces.map(w=><tr key={w.id}><td>{w.name}</td><td>{w.role}</td><td>{w.access_role}</td><td>{w.organization_id??"Personal"}</td><td><button className="button" disabled={w.id===workspaceId} onClick={()=>switchWorkspace(w.id)}>{w.id===workspaceId?"Active":"Use"}</button></td></tr>)}</tbody></table></div></section>

    <section className="panel" data-testid="active-workspace-settings"><h2>Active workspace settings</h2>
      {canManage?<><p className="sectionLead">OWNER and ADMIN access may update the workspace display name and operating context.</p><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Workspace name<input value={editName} onChange={e=>setEditName(e.target.value)}/></label><label className="field">Context<select value={editRole} onChange={e=>setEditRole(e.target.value)}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label><button className="button" disabled={updateWs.isPending||editName.trim().length<2} onClick={()=>updateWs.mutate({workspaceId,name:editName.trim(),role:editRole})}>{updateWs.isPending?"Saving…":"Save workspace changes"}</button></div>{updateWs.isError?<p className="error" role="alert">Rivexis could not update this workspace. Your previous settings remain authoritative.</p>:null}</>:<p>Workspace editing requires OWNER or ADMIN access. Your current role is <b>{workspace.access_role}</b>.</p>}
    </section>

    <section className="panel"><h2>Create personal workspace</h2><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Name<input value={name} onChange={e=>setName(e.target.value)}/></label><label className="field">Context<select value={role} onChange={e=>setRole(e.target.value)}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label><button className="button" disabled={makeWs.isPending||name.trim().length<2} onClick={()=>makeWs.mutate()}>{makeWs.isPending?"Creating…":"Create"}</button></div>{makeWs.isError?<p className="error" role="alert">Rivexis could not create the workspace. Review the input and retry.</p>:null}</section>

    <section className="panel"><h2>Organizations</h2>{orgs.isPending?<p>Loading organizations…</p>:null}{orgs.isError?<p className="error" role="alert">Rivexis could not load organizations for this account.</p>:null}{!orgs.isPending&&!orgs.isError&&!orgs.data?.items.length?<p>No organizations are linked to this account yet.</p>:null}{!orgs.isPending&&!orgs.isError&&orgs.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Your role</th><th>Created</th></tr></thead><tbody>{orgs.data.items.map(org=><tr key={org.id}><td>{org.name}</td><td>{org.member_role}</td><td>{org.created_at?new Date(org.created_at).toLocaleString():"—"}</td></tr>)}</tbody></table></div>:null}<div style={{display:"flex",gap:12,marginTop:12}}><input value={orgName} onChange={e=>setOrgName(e.target.value)} style={{flex:1}} aria-label="Organization name"/><button className="button" disabled={makeOrg.isPending||orgName.trim().length<2} onClick={()=>makeOrg.mutate()}>{makeOrg.isPending?"Creating…":"Create organization"}</button></div>{makeOrg.isError?<p className="error" role="alert">Rivexis could not create the organization. Review the input and retry.</p>:null}</section>

    <section className="panel" data-testid="workspace-admin-activity"><h2>Administrative activity</h2>{canManage?<>{audit.isPending?<p>Loading the latest administrative events…</p>:null}{audit.isError?<p className="error" role="alert">Administrative activity is unavailable. Rivexis has not substituted unverified events.</p>:null}{!audit.isPending&&!audit.isError&&!audit.data?.items.length?<p>No workspace administrative events are recorded yet.</p>:null}{!audit.isPending&&!audit.isError&&audit.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Time</th><th>Action</th><th>Resource</th><th>Actor</th></tr></thead><tbody>{audit.data.items.map(row=><tr key={row.id}><td>{new Date(row.created_at).toLocaleString()}</td><td>{row.action}</td><td>{row.resource_type}</td><td>{row.actor??"System/unknown"}</td></tr>)}</tbody></table></div>:null}</>:<p>Administrative audit activity requires OWNER or ADMIN access. Rivexis does not request or expose it for your current role.</p>}</section>
  </>;
}
