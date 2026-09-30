"use client";

import {useEffect,useMemo,useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {ApiError,api} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

type Workspace={id:string;name:string;role:string;organization_id?:string|null;access_role:string;created_at?:string};
type Org={id:string;name:string;member_role:string;created_at:string};
type OrgMember={user_id:string;email:string;role:string;created_at:string};
type MembersResponse={items:OrgMember[];member_role:string};
type MembershipClaim={organization_id:string;claim_token:string;expires_in_seconds:number;expires_at?:string};

const ORG_ROLES=["OWNER","ADMIN","ANALYST","VIEWER"] as const;

function listError(error:unknown,kind:"workspaces"|"organizations"){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could load these settings.";
    if(error.status===403)return kind==="organizations"?"Organization access could not be confirmed for this account.":"Workspace access could not be confirmed for this account.";
    if(error.status===503)return "Settings are temporarily unavailable because the application API is unavailable.";
  }
  return kind==="organizations"?"Rivexis could not load organizations for this account.":"Rivexis could not load your authorized workspaces.";
}

function membershipError(error:unknown){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could complete this membership action.";
    if(error.status===403)return "Your current organization role does not permit this membership action.";
    if(error.status===404)return "Rivexis could not confirm the requested organization, member, or account.";
    if(error.status===409)return "The membership action conflicts with current organization state. The claim may be invalid or expired, or the last-owner safeguard may apply.";
    if(error.status===422)return "Review the organization, role, and membership claim fields, then retry.";
    if(error.status===503)return "Organization membership is temporarily unavailable because the application API is unavailable.";
  }
  return "Rivexis could not complete the membership action safely.";
}

function createdAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}

function expiryLabel(value?:string,seconds?:number){
  if(value){const date=new Date(value);if(!Number.isNaN(date.getTime()))return date.toLocaleString()}
  if(typeof seconds==="number")return `approximately ${Math.max(1,Math.round(seconds/60))} minutes from creation`;
  return "15 minutes from creation";
}

export default function Settings(){
  const qc=useQueryClient();
  const {workspaceId,switchWorkspace}=useWorkspace();
  const [name,setName]=useState("Institutional Workspace");
  const [role,setRole]=useState("Analyst");
  const [orgName,setOrgName]=useState("Rivexis Organization");
  const [selectedOrgId,setSelectedOrgId]=useState("");
  const [roleDrafts,setRoleDrafts]=useState<Record<string,string>>({});
  const [claimToken,setClaimToken]=useState("");
  const [claimRole,setClaimRole]=useState("ANALYST");
  const [joinOrgId,setJoinOrgId]=useState("");
  const [generatedClaim,setGeneratedClaim]=useState<MembershipClaim|null>(null);
  const [pendingRemove,setPendingRemove]=useState("");

  const ws=useQuery({queryKey:["workspace-settings"],queryFn:()=>api<{items:Workspace[]}>("/api/v1/workspaces"),retry:false});
  const orgs=useQuery({queryKey:["organizations"],queryFn:()=>api<{items:Org[]}>("/api/v1/organizations"),retry:false});

  useEffect(()=>{
    const items=orgs.data?.items??[];
    if(!items.length){setSelectedOrgId("");return}
    if(!items.some(org=>org.id===selectedOrgId))setSelectedOrgId(items[0].id);
  },[orgs.data?.items,selectedOrgId]);

  const selectedOrg=useMemo(()=>orgs.data?.items.find(org=>org.id===selectedOrgId)??null,[orgs.data?.items,selectedOrgId]);
  const members=useQuery({
    queryKey:["organization-members",selectedOrgId],
    queryFn:()=>api<MembersResponse>(`/api/v1/organizations/${encodeURIComponent(selectedOrgId)}/members`),
    enabled:Boolean(selectedOrgId),retry:false,
  });

  useEffect(()=>{
    const next:Record<string,string>={};
    for(const member of members.data?.items??[])next[member.user_id]=member.role;
    setRoleDrafts(next);
    setPendingRemove("");
  },[members.data?.items,selectedOrgId]);

  useEffect(()=>{
    setClaimToken("");
    setClaimRole("ANALYST");
    setPendingRemove("");
  },[selectedOrgId]);

  const memberRole=members.data?.member_role??selectedOrg?.member_role??"";
  const canAdmin=memberRole==="OWNER"||memberRole==="ADMIN";
  const roleChoices=memberRole==="OWNER"?ORG_ROLES:ORG_ROLES.filter(value=>value!=="OWNER");

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
      setSelectedOrgId(r.id);
      void qc.invalidateQueries({queryKey:["organizations"]});
    }
  });

  const updateMember=useMutation({
    mutationFn:({orgId,member,nextRole}:{orgId:string;member:OrgMember;nextRole:string})=>api<OrgMember>(`/api/v1/organizations/${encodeURIComponent(orgId)}/members`,{method:"POST",body:JSON.stringify({email:member.email,role:nextRole})}),
    onSuccess:(r,{orgId})=>{
      qc.setQueryData<MembersResponse>(["organization-members",orgId],old=>old?{...old,items:old.items.map(member=>member.user_id===r.user_id?{...member,...r}:member)}:old);
      if(selectedOrgId===orgId)setRoleDrafts(current=>({...current,[r.user_id]:r.role}));
    }
  });

  const acceptClaim=useMutation({
    mutationFn:({orgId,token,nextRole}:{orgId:string;token:string;nextRole:string})=>api<OrgMember>(`/api/v1/organizations/${encodeURIComponent(orgId)}/members/claim`,{method:"POST",body:JSON.stringify({claim_token:token,role:nextRole})}),
    onSuccess:(r,{orgId})=>{
      qc.setQueryData<MembersResponse>(["organization-members",orgId],old=>old?{...old,items:[...old.items.filter(member=>member.user_id!==r.user_id),r]}:old);
      if(selectedOrgId===orgId){
        setRoleDrafts(current=>({...current,[r.user_id]:r.role}));
        setClaimToken("");
      }
    }
  });

  const removeMember=useMutation({
    mutationFn:({orgId,member}:{orgId:string;member:OrgMember})=>api<void>(`/api/v1/organizations/${encodeURIComponent(orgId)}/members/${encodeURIComponent(member.user_id)}`,{method:"DELETE"}),
    onSuccess:(_, {orgId,member})=>{
      qc.setQueryData<MembersResponse>(["organization-members",orgId],old=>old?{...old,items:old.items.filter(item=>item.user_id!==member.user_id)}:old);
      if(selectedOrgId===orgId)setPendingRemove("");
    }
  });

  const createClaim=useMutation({
    mutationFn:(orgId:string)=>api<MembershipClaim>(`/api/v1/organizations/${encodeURIComponent(orgId)}/membership-claim`,{method:"POST",body:JSON.stringify({})}),
    onMutate:()=>setGeneratedClaim(null),
    onSuccess:r=>setGeneratedClaim(r),
  });

  const updateMemberCurrent=updateMember.variables?.orgId===selectedOrgId;
  const acceptClaimCurrent=acceptClaim.variables?.orgId===selectedOrgId;
  const removeMemberCurrent=removeMember.variables?.orgId===selectedOrgId;
  const membershipMutationError=updateMemberCurrent&&updateMember.error?updateMember.error:acceptClaimCurrent&&acceptClaim.error?acceptClaim.error:removeMemberCurrent&&removeMember.error?removeMember.error:null;
  const membershipBusy=updateMember.isPending||acceptClaim.isPending||removeMember.isPending;

  return <>
    <div className="workspaceHeader"><div><h1>Workspaces & Organizations</h1><p>Operate personal workspaces, organization membership, and access roles from one evidence-boundary-aware control surface.</p></div><span className="badge">ACTIVE {workspaceId}</span></div>

    <section className="panel"><h2>Your workspaces</h2>
      {ws.isPending?<p>Loading authorized workspaces…</p>:null}
      {ws.isError?<p className="error" role="alert">{listError(ws.error,"workspaces")}</p>:null}
      {!ws.isPending&&!ws.isError&&!ws.data?.items.length?<p>No workspaces are currently authorized for this account.</p>:null}
      {!ws.isPending&&!ws.isError&&ws.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Context</th><th>Access</th><th>Organization</th><th>Action</th></tr></thead><tbody>{ws.data.items.map(w=><tr key={w.id}><td>{w.name}</td><td>{w.role}</td><td>{w.access_role}</td><td>{w.organization_id??"Personal"}</td><td><button className="button" type="button" disabled={w.id===workspaceId} onClick={()=>switchWorkspace(w.id)}>{w.id===workspaceId?"Active":"Use"}</button></td></tr>)}</tbody></table></div>:null}
    </section>

    <section className="panel"><h2>Create personal workspace</h2><p className="sectionLead">A personal workspace is owned by the current account. It does not create organization membership or grant access to other users.</p><div style={{display:"grid",gridTemplateColumns:"2fr 1fr auto",gap:12,alignItems:"end"}}><label className="field">Name<input value={name} onChange={e=>setName(e.target.value)}/></label><label className="field">Context<select value={role} onChange={e=>setRole(e.target.value)}><option>Individual</option><option>Fund</option><option>Treasury</option><option>Analyst</option></select></label><button className="button" type="button" disabled={makeWs.isPending||name.trim().length<2} onClick={()=>makeWs.mutate()}>{makeWs.isPending?"Creating…":"Create"}</button></div>{makeWs.isSuccess?<p role="status">Created <b>{makeWs.data.name}</b> and made it the active workspace.</p>:null}{makeWs.isError?<p className="error" role="alert">Rivexis could not create the workspace. Review the input and retry.</p>:null}</section>

    <section className="panel"><div className="panelHeading"><div><span className="workspaceKicker">Organization control</span><h2>Organizations</h2><p className="sectionLead">Organization IDs are explicit because authenticated membership claims use them as the target boundary. Possessing an ID alone never grants access.</p></div>{selectedOrg?<span className="badge">{memberRole||selectedOrg.member_role}</span>:null}</div>
      {orgs.isPending?<p>Loading organizations…</p>:null}
      {orgs.isError?<p className="error" role="alert">{listError(orgs.error,"organizations")}</p>:null}
      {!orgs.isPending&&!orgs.isError&&!orgs.data?.items.length?<p>No organizations are currently associated with this account.</p>:null}
      {!orgs.isPending&&!orgs.isError&&orgs.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Name</th><th>Organization ID</th><th>Your role</th><th>Created</th><th>Action</th></tr></thead><tbody>{orgs.data.items.map(org=><tr key={org.id}><td>{org.name}</td><td><code>{org.id}</code></td><td>{org.member_role}</td><td>{createdAt(org.created_at)}</td><td><button className={org.id===selectedOrgId?"button":"ghost"} type="button" disabled={membershipBusy} onClick={()=>setSelectedOrgId(org.id)}>{org.id===selectedOrgId?"Selected":"Manage"}</button></td></tr>)}</tbody></table></div>:null}
      <div style={{display:"flex",gap:12,marginTop:16,alignItems:"end",flexWrap:"wrap"}}><label className="field" style={{flex:"1 1 260px"}}>Organization name<input value={orgName} onChange={e=>setOrgName(e.target.value)}/></label><button className="button" type="button" disabled={makeOrg.isPending||orgName.trim().length<2} onClick={()=>makeOrg.mutate()}>{makeOrg.isPending?"Creating…":"Create organization"}</button></div>
      {makeOrg.isSuccess?<p role="status">Created <b>{makeOrg.data.name}</b>. Your membership role is {makeOrg.data.member_role}.</p>:null}{makeOrg.isError?<p className="error" role="alert">Rivexis could not create the organization. Review the input and retry.</p>:null}
    </section>

    {selectedOrg?<section className="panel" data-testid="organization-member-admin"><div className="panelHeading"><div><span className="workspaceKicker">Authenticated membership</span><h2>{selectedOrg.name} members</h2><p className="sectionLead">Existing members can have roles changed by authorized organization administrators. New members are accepted only from short-lived claims generated by the target authenticated account.</p></div><span className="stepLabel">{selectedOrg.id}</span></div>
      {members.isPending?<p>Loading organization members…</p>:null}
      {members.isError?<p className="error" role="alert">{membershipError(members.error)}</p>:null}
      {!members.isPending&&!members.isError&&members.data?.items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Member</th><th>Role</th><th>Joined</th><th>Controls</th></tr></thead><tbody>{members.data.items.map(member=>{
        const draft=roleDrafts[member.user_id]??member.role;
        const ownerRestricted=memberRole!=="OWNER"&&member.role==="OWNER";
        return <tr key={member.user_id} data-testid="organization-member-row"><td><b>{member.email}</b><small style={{display:"block"}}>{member.user_id}</small></td><td><select aria-label={`Role for ${member.email}`} value={draft} disabled={!canAdmin||ownerRestricted||membershipBusy} onChange={e=>setRoleDrafts(current=>({...current,[member.user_id]:e.target.value}))}>{(memberRole==="OWNER"?ORG_ROLES:ORG_ROLES.filter(value=>value!=="OWNER")).map(value=><option key={value} value={value}>{value}</option>)}</select></td><td>{createdAt(member.created_at)}</td><td><div className="actions"><button className="button" type="button" aria-label={`Update ${member.email}`} disabled={!canAdmin||ownerRestricted||draft===member.role||membershipBusy} onClick={()=>updateMember.mutate({orgId:selectedOrgId,member,nextRole:draft})}>Update role</button><button className="ghost" type="button" aria-label={pendingRemove===member.user_id?`Confirm remove ${member.email}`:`Remove ${member.email}`} disabled={!canAdmin||ownerRestricted||membershipBusy} onClick={()=>pendingRemove===member.user_id?removeMember.mutate({orgId:selectedOrgId,member}):setPendingRemove(member.user_id)}>{pendingRemove===member.user_id?"Confirm remove":"Remove"}</button></div></td></tr>;
      })}</tbody></table></div>:null}
      {!members.isPending&&!members.isError&&!members.data?.items.length?<p>No members were returned for this organization.</p>:null}
      {!canAdmin&&!members.isPending&&!members.isError?<p className="muted">Your {memberRole||"current"} role can inspect membership but cannot change roles or accept/remove members.</p>:null}
      {membershipMutationError?<p className="error" role="alert">{membershipError(membershipMutationError)}</p>:null}
      {updateMemberCurrent&&updateMember.isSuccess?<p role="status">Updated {updateMember.data.email} to {updateMember.data.role}.</p>:null}
      {removeMemberCurrent&&removeMember.isSuccess?<p role="status">Organization member removed.</p>:null}

      <div className="advancedOnly"><div className="panelHeading"><div><b>Accept authenticated membership claim</b><p>Do not add a new person by email alone. The intended member signs in, generates a short-lived opaque claim for this organization ID, and shares that claim with an OWNER or ADMIN.</p></div><span className="stepLabel">CLAIM REQUIRED</span></div><div style={{display:"grid",gridTemplateColumns:"minmax(0,2fr) minmax(140px,.6fr) auto",gap:12,alignItems:"end"}}><label className="field">Membership claim token<input aria-label="Membership claim token" value={claimToken} onChange={e=>setClaimToken(e.target.value)} placeholder="Paste the member's short-lived claim"/></label><label className="field">Claim role<select aria-label="Claim role" value={claimRole} disabled={!canAdmin||membershipBusy} onChange={e=>setClaimRole(e.target.value)}>{roleChoices.map(value=><option key={value} value={value}>{value}</option>)}</select></label><button className="button" type="button" disabled={!canAdmin||membershipBusy||claimToken.trim().length<32} onClick={()=>acceptClaim.mutate({orgId:selectedOrgId,token:claimToken.trim(),nextRole:claimRole})}>{acceptClaim.isPending?"Accepting…":"Accept claim"}</button></div>{acceptClaimCurrent&&acceptClaim.isSuccess?<p role="status">Accepted authenticated membership for <b>{acceptClaim.data.email}</b> as {acceptClaim.data.role}.</p>:null}{acceptClaimCurrent&&acceptClaim.isError?<p className="error" role="alert">{membershipError(acceptClaim.error)}</p>:null}</div>
    </section>:null}

    <section className="panel" data-testid="membership-claim-generator"><div className="panelHeading"><div><span className="workspaceKicker">Join boundary</span><h2>Generate my membership claim</h2><p className="sectionLead">Use the organization ID supplied by its administrator. Rivexis creates a one-time opaque token tied to your authenticated account; it does not add you to the organization by itself.</p></div><span className="stepLabel">15 MINUTES</span></div><div style={{display:"grid",gridTemplateColumns:"minmax(0,1fr) auto",gap:12,alignItems:"end"}}><label className="field">Organization ID<input aria-label="Organization ID for membership claim" value={joinOrgId} disabled={createClaim.isPending} onChange={e=>{setJoinOrgId(e.target.value);setGeneratedClaim(null)}} placeholder="Organization ID shared by the administrator"/></label><button className="button" type="button" disabled={createClaim.isPending||joinOrgId.trim().length<3} onClick={()=>createClaim.mutate(joinOrgId.trim())}>{createClaim.isPending?"Generating…":"Generate claim"}</button></div>
      {generatedClaim?<div className="advancedOnly" data-testid="generated-membership-claim"><b>One-time membership claim</b><p>Share this token only with the intended organization OWNER or ADMIN. A new claim invalidates your previous unused claim for the same organization.</p><small>Target organization: <code>{generatedClaim.organization_id}</code></small><code style={{display:"block",overflowWrap:"anywhere",padding:"12px 0"}}>{generatedClaim.claim_token}</code><small>Expires {expiryLabel(generatedClaim.expires_at,generatedClaim.expires_in_seconds)}.</small></div>:null}
      {createClaim.isError?<p className="error" role="alert">{membershipError(createClaim.error)}</p>:null}
    </section>
  </>;
}
