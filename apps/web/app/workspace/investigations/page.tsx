"use client";

import {useEffect,useRef,useState} from "react";
import {api,apiBlob} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

type CaseRow={id:string;status:string;created_at:string;payload:{title?:string;notes?:string;disposition?:string|null;review_ids?:string[];timeline?:{event_count?:number;events?:unknown[]}}};

export default function InvestigationsPage(){
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const epochRef=useRef(0);
  const [items,setItems]=useState<CaseRow[]>([]);const [selected,setSelected]=useState<CaseRow|null>(null);
  const [title,setTitle]=useState("");const [adapter,setAdapter]=useState("aave_v3");const [chain,setChain]=useState("ethereum");const [fromBlock,setFrom]=useState("");const [toBlock,setTo]=useState("");const [subject,setSubject]=useState("");const [notes,setNotes]=useState("");const [disposition,setDisposition]=useState("");const [reviewId,setReviewId]=useState("");const [error,setError]=useState("");const [busy,setBusy]=useState(false);

  async function load(targetWorkspace=workspaceId,epoch=epochRef.current){
    try{
      const r=await api<{items:CaseRow[]}>(`/api/v1/protocol-investigations?workspace_id=${encodeURIComponent(targetWorkspace)}`);
      if(workspaceRef.current!==targetWorkspace||epochRef.current!==epoch)return;
      setItems(r.items);
      setSelected(current=>current?r.items.find(x=>x.id===current.id)??null:null);
    }catch{
      if(workspaceRef.current===targetWorkspace&&epochRef.current===epoch)setError("Rivexis could not load investigations for this workspace.");
    }
  }

  useEffect(()=>{
    workspaceRef.current=workspaceId;
    epochRef.current+=1;
    const epoch=epochRef.current;
    setItems([]);setSelected(null);setNotes("");setDisposition("");setReviewId("");setError("");setBusy(false);
    void load(workspaceId,epoch);
  },[workspaceId]);

  function input(){const x:Record<string,unknown>={protocol_adapter:adapter,chain,from_block:fromBlock,to_block:toBlock,hydrate_timestamps:true};if(adapter==="aave_v3"&&subject)x.asset_address=subject;if(adapter==="compound_v3"){x.compound_market="usdc";if(subject)x.collateral_asset=subject}if(adapter==="morpho_blue"&&subject)x.morpho_market_id=subject;return x}

  async function createCase(){
    const originWorkspace=workspaceId;const epoch=epochRef.current;
    setBusy(true);setError("");
    try{
      const row=await api<CaseRow>("/api/v1/protocol-investigations",{method:"POST",body:JSON.stringify({workspace_id:originWorkspace,title,input:input(),notes})});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      setTitle("");setNotes("");setSelected(row);await load(originWorkspace,epoch);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not create the investigation. Review the input and provider availability, then retry.");}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setBusy(false)}
  }

  async function update(status?:string){
    if(!selected)return;const originWorkspace=workspaceId;const epoch=epochRef.current;const caseId=selected.id;
    setBusy(true);setError("");
    try{
      const row=await api<CaseRow>(`/api/v1/protocol-investigations/${caseId}`,{method:"PATCH",body:JSON.stringify({status,notes,disposition})});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      setSelected(row);await load(originWorkspace,epoch);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not update this investigation.");}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setBusy(false)}
  }

  async function attach(){
    if(!selected||!reviewId)return;const originWorkspace=workspaceId;const epoch=epochRef.current;const caseId=selected.id;const targetReview=reviewId;
    setBusy(true);setError("");
    try{
      const row=await api<CaseRow>(`/api/v1/protocol-investigations/${caseId}/reviews/${targetReview}`,{method:"POST"});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      setSelected(row);setReviewId("");await load(originWorkspace,epoch);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not attach that review to this investigation.");}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setBusy(false)}
  }

  async function pdf(){
    if(!selected)return;const originWorkspace=workspaceId;const epoch=epochRef.current;const caseId=selected.id;
    try{
      const blob=await apiBlob(`/api/v1/protocol-investigations/${caseId}/render?format=pdf`);
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      const url=URL.createObjectURL(blob);window.open(url,"_blank","noopener,noreferrer");setTimeout(()=>URL.revokeObjectURL(url),60000);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not render this investigation report.");}
  }

  return <>
    <div className="workspaceHeader"><div><h1>Protocol Investigations</h1><p>Preserve a protocol event timeline, attach configuration reviews, record analyst notes and disposition, and close only with an explicit conclusion.</p></div><span className="badge">{workspace.name}</span></div>
    <section className="panel"><h2>Open investigation</h2><div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:12}}><label className="field">Title<input value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g. Aave WETH risk parameter review"/></label><label className="field">Protocol<select value={adapter} onChange={e=>setAdapter(e.target.value)}><option value="aave_v3">Aave V3</option><option value="compound_v3">Compound III</option><option value="morpho_blue">Morpho Blue</option></select></label><label className="field">Chain<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option></select></label><label className="field">From block<input value={fromBlock} onChange={e=>setFrom(e.target.value)}/></label><label className="field">To block<input value={toBlock} onChange={e=>setTo(e.target.value)}/></label><label className="field">Asset / market ID<input value={subject} onChange={e=>setSubject(e.target.value)} placeholder="0x…"/></label></div><label className="field" style={{marginTop:12}}>Opening notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={3}/></label><button className="button" disabled={busy||title.length<2||!fromBlock||!toBlock} onClick={createCase}>{busy?"Working…":"Create investigation"}</button>{error?<p className="error" role="alert">{error}</p>:null}</section>
    <section className="panel" aria-live="polite" data-testid="workspace-investigations-state"><h2>Cases · {workspace.name}</h2><div style={{overflowX:"auto"}}><table><thead><tr><th>Created</th><th>Title</th><th>Status</th><th>Events</th><th>Reviews</th></tr></thead><tbody>{items.length?items.map(x=><tr key={x.id} onClick={()=>{setSelected(x);setNotes(x.payload.notes??"");setDisposition(x.payload.disposition??"")}} style={{cursor:"pointer"}}><td>{new Date(x.created_at).toLocaleString()}</td><td><b>{x.payload.title??x.id}</b></td><td>{x.status}</td><td>{x.payload.timeline?.event_count??0}</td><td>{x.payload.review_ids?.length??0}</td></tr>):<tr><td colSpan={5}>No investigation cases in this workspace.</td></tr>}</tbody></table></div></section>
    {selected?<section className="panel" data-testid="investigation-selected"><h2>{selected.payload.title}</h2><p><b>Case ID:</b> <code>{selected.id}</code> · <b>Status:</b> {selected.status}</p><label className="field">Analyst notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={4}/></label><label className="field">Disposition<textarea value={disposition} onChange={e=>setDisposition(e.target.value)} rows={3} placeholder="Required before closing"/></label><div style={{display:"flex",gap:8,flexWrap:"wrap"}}><button className="button" disabled={busy} onClick={()=>update("in_review")}>Save / mark in review</button><button className="button" disabled={busy||!disposition.trim()} onClick={()=>update("closed")}>Close with disposition</button><button className="button" disabled={busy} onClick={pdf}>Open PDF</button></div><div style={{marginTop:14,display:"flex",gap:8}}><input value={reviewId} onChange={e=>setReviewId(e.target.value)} placeholder="Configuration review ID"/><button className="button" disabled={busy||!reviewId} onClick={attach}>Attach review</button></div><p><b>Linked reviews:</b> {(selected.payload.review_ids??[]).join(", ")||"None"}</p></section>:null}
  </>;
}
