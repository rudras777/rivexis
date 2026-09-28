"use client";

import {useEffect,useRef,useState} from "react";
import {api} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

type CaseRow={id:string;status:string;created_at:string;payload:{title?:string;notes?:string;disposition?:string|null;review_ids?:string[];timeline?:{event_count?:number;events?:unknown[]}}};

function normalizeCase(row:CaseRow):CaseRow{return {...row,payload:row.payload??{}}}
function isBlock(value:string){return /^(0|[1-9]\d{0,15})$/.test(value)&&BigInt(value)<=BigInt(Number.MAX_SAFE_INTEGER)}
function validRange(from:string,to:string){return isBlock(from)&&isBlock(to)&&BigInt(from)<=BigInt(to)}
function isEvmAddress(value:string){return /^0x[a-fA-F0-9]{40}$/.test(value)}
function isBytes32(value:string){return /^0x[a-fA-F0-9]{64}$/.test(value)}
function recordedAt(value:string){const date=new Date(value);return Number.isNaN(date.getTime())?value:date.toLocaleString()}

export default function InvestigationsPage(){
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const epochRef=useRef(0);
  const [items,setItems]=useState<CaseRow[]>([]);
  const [selected,setSelected]=useState<CaseRow|null>(null);
  const [title,setTitle]=useState("");
  const [adapter,setAdapter]=useState("aave_v3");
  const [chain,setChain]=useState("ethereum");
  const [fromBlock,setFrom]=useState("");
  const [toBlock,setTo]=useState("");
  const [subject,setSubject]=useState("");
  const [notes,setNotes]=useState("");
  const [disposition,setDisposition]=useState("");
  const [reviewId,setReviewId]=useState("");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [loading,setLoading]=useState(true);

  async function load(targetWorkspace=workspaceId,epoch=epochRef.current){
    setLoading(true);
    try{
      const response=await api<{items:CaseRow[]}>(`/api/v1/protocol-investigations?workspace_id=${encodeURIComponent(targetWorkspace)}`);
      if(workspaceRef.current!==targetWorkspace||epochRef.current!==epoch)return;
      const rows=response.items.map(normalizeCase);setItems(rows);setError("");
      setSelected(current=>current?rows.find(item=>item.id===current.id)??null:null);
    }catch{if(workspaceRef.current===targetWorkspace&&epochRef.current===epoch)setError("Rivexis could not load investigations for this workspace.")}
    finally{if(workspaceRef.current===targetWorkspace&&epochRef.current===epoch)setLoading(false)}
  }

  useEffect(()=>{
    workspaceRef.current=workspaceId;epochRef.current+=1;
    const epoch=epochRef.current;
    setItems([]);setSelected(null);setNotes("");setDisposition("");setReviewId("");setError("");setBusy(false);setLoading(true);
    void load(workspaceId,epoch);
  },[workspaceId]);

  function changeAdapter(next:string){setAdapter(next);setSubject("");setError("")}
  function input(){const x:Record<string,unknown>={protocol_adapter:adapter,chain,from_block:fromBlock,to_block:toBlock,hydrate_timestamps:true};if(adapter==="aave_v3"&&subject)x.asset_address=subject;if(adapter==="compound_v3"){x.compound_market="usdc";if(subject)x.collateral_asset=subject}if(adapter==="morpho_blue"&&subject)x.morpho_market_id=subject;return x}
  function selectCase(row:CaseRow){setSelected(row);setNotes(row.payload.notes??"");setDisposition(row.payload.disposition??"");setReviewId("");setError("")}

  async function createCase(){
    const originWorkspace=workspaceId;const epoch=epochRef.current;
    setBusy(true);setError("");
    try{
      const row=await api<CaseRow>("/api/v1/protocol-investigations",{method:"POST",body:JSON.stringify({workspace_id:originWorkspace,title:title.trim(),input:input(),notes:notes.trim()})});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      const normalized=normalizeCase(row);setTitle("");setNotes(normalized.payload.notes??"");setDisposition(normalized.payload.disposition??"");setSelected(normalized);await load(originWorkspace,epoch);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not create the investigation. Review the input and provider availability, then retry.")}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setBusy(false)}
  }

  async function update(status:"in_review"|"closed"){
    if(!selected)return;const originWorkspace=workspaceId;const epoch=epochRef.current;const caseId=selected.id;
    setBusy(true);setError("");
    try{
      const row=await api<CaseRow>(`/api/v1/protocol-investigations/${encodeURIComponent(caseId)}`,{method:"PATCH",body:JSON.stringify({status,notes:notes.trim(),disposition:disposition.trim()})});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      setSelected(normalizeCase(row));await load(originWorkspace,epoch);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not update this investigation.")}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setBusy(false)}
  }

  async function attach(){
    if(!selected||!reviewId.trim())return;const originWorkspace=workspaceId;const epoch=epochRef.current;const caseId=selected.id;const targetReview=reviewId.trim();
    setBusy(true);setError("");
    try{
      const row=await api<CaseRow>(`/api/v1/protocol-investigations/${encodeURIComponent(caseId)}/reviews/${encodeURIComponent(targetReview)}`,{method:"POST"});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      setSelected(normalizeCase(row));setReviewId("");await load(originWorkspace,epoch);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not attach that review to this investigation.")}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setBusy(false)}
  }

  const rangeValid=validRange(fromBlock,toBlock);
  const subjectValid=!subject||(adapter==="morpho_blue"?isBytes32(subject):isEvmAddress(subject));
  const createValid=title.trim().length>=2&&rangeValid&&subjectValid;
  const openCount=items.filter(item=>item.status.toLowerCase()==="open").length;
  const reviewCount=items.filter(item=>item.status.toLowerCase()==="in_review").length;
  const closedCount=items.filter(item=>item.status.toLowerCase()==="closed").length;
  const subjectLabel=adapter==="morpho_blue"?"Market ID (bytes32)":adapter==="compound_v3"?"Collateral asset":"Reserve asset";

  return <>
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">Analyst case management</div><h1>Protocol investigations</h1><p>Preserve evidence, attach approved reviews and close cases only with an explicit disposition.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name}</span><span className="badge">WORKSPACE ARTIFACTS</span></div></div>
    <section className="overviewBand surfaceOverview" aria-label="Investigation overview"><div><small>TOTAL CASES</small><strong>{loading?"—":items.length}</strong><span>Authorized workspace records</span></div><div><small>OPEN</small><strong>{loading?"—":openCount}</strong><span>Evidence gathering</span></div><div><small>IN REVIEW</small><strong>{loading?"—":reviewCount}</strong><span>Analyst assessment</span></div><div><small>CLOSED</small><strong>{loading?"—":closedCount}</strong><span>Disposition recorded</span></div></section>
    <div className="truthNotice"><span className="statusDot"/>A closed case records analyst disposition and evidence lineage. It does not certify protocol safety or fill missing provider evidence.</div>
    <section className="panel operationalPanel">
      <div className="panelHeading"><div><span className="workspaceKicker">New case</span><h2>Open investigation</h2></div><p className="sectionLead">Create a workspace-scoped case from a validated protocol identity and bounded block range.</p></div>
      <div className="protocolFormGrid">
        <label className="field wideField">Case title<input value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g. Aave WETH parameter review"/></label>
        <label className="field">Protocol<select value={adapter} onChange={e=>changeAdapter(e.target.value)}><option value="aave_v3">Aave V3</option><option value="compound_v3">Compound III</option><option value="morpho_blue">Morpho Blue</option></select></label>
        <label className="field">Network<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option></select></label>
        <label className="field">From block<input inputMode="numeric" aria-invalid={fromBlock.length>0&&!isBlock(fromBlock)} value={fromBlock} onChange={e=>setFrom(e.target.value)} placeholder="e.g. 21000000"/></label>
        <label className="field">To block<input inputMode="numeric" aria-invalid={toBlock.length>0&&!isBlock(toBlock)} value={toBlock} onChange={e=>setTo(e.target.value)} placeholder="e.g. 21010000"/></label>
        <label className="field">{subjectLabel}<input aria-invalid={subject.length>0&&!subjectValid} value={subject} onChange={e=>setSubject(e.target.value.trim())} placeholder={adapter==="morpho_blue"?"Optional 0x + 64 hex":"Optional 0x + 40 hex"}/></label>
      </div>
      {(fromBlock||toBlock)&&!rangeValid?<p className="fieldError" role="status">Enter a complete block range with the from block less than or equal to the to block.</p>:null}
      {subject&&!subjectValid?<p className="fieldError" role="status">Enter the complete hexadecimal identity required by the selected protocol adapter.</p>:null}
      <label className="field notesField">Opening notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={3} placeholder="Record the question, observed condition and evidence still required."/></label>
      <div className="actionBar"><div><span>CASE READINESS</span><small>{createValid?"Validated case ready to persist":"Title and valid block range are required"}</small></div><button className="button" type="button" disabled={busy||!createValid} onClick={createCase}>{busy?"Creating…":"Create investigation"}</button></div>
      {error&&!selected?<p className="error" role="alert">{error}</p>:null}
    </section>

    <section className="panel operationalPanel" aria-live="polite" data-testid="workspace-investigations-state">
      <div className="panelHeading"><div><span className="workspaceKicker">Authorized casebook</span><h2>Cases · {workspace.name}</h2></div><p className="sectionLead">Select a case to review notes, linked configuration reviews and disposition.</p></div>
      {loading?<div className="surfaceState" role="status">Loading investigation cases…</div>:null}
      {!loading&&error&&!selected?<p className="error" role="alert">{error}</p>:null}
      {!loading&&!error&&!items.length?<div className="surfaceState"><b>No investigation cases in this workspace.</b><span>Open the first bounded case above; Rivexis will not synthesize events or conclusions.</span></div>:null}
      {!loading&&items.length?<div className="tableWrap"><table className="table"><thead><tr><th>Created</th><th>Case</th><th>Status</th><th>Events</th><th>Reviews</th><th>Action</th></tr></thead><tbody>{items.map(item=><tr key={item.id}><td>{recordedAt(item.created_at)}</td><td><button className="tableTitleButton" type="button" onClick={()=>selectCase(item)}>{item.payload.title??item.id}</button><br/><code>{item.id}</code></td><td><span className={`statePill ${item.status.toLowerCase()==="closed"?"positive":item.status.toLowerCase()==="in_review"?"warning":"neutral"}`}>{item.status}</span></td><td>{item.payload.timeline?.event_count??0}</td><td>{item.payload.review_ids?.length??0}</td><td><button className="ghost compactButton" type="button" aria-expanded={selected?.id===item.id} onClick={()=>selectCase(item)}>{selected?.id===item.id?"Selected":"Review case"}</button></td></tr>)}</tbody></table></div>:null}
    </section>

    {selected?<section className="panel artifactWorkspace" data-testid="investigation-selected">
      <div className="panelHeading"><div><span className="workspaceKicker">Selected investigation</span><h2>{selected.payload.title??selected.id}</h2><p className="sectionLead"><code>{selected.id}</code></p></div><span className={`statePill ${selected.status.toLowerCase()==="closed"?"positive":selected.status.toLowerCase()==="in_review"?"warning":"neutral"}`}>{selected.status}</span></div>
      <div className="artifactEditorGrid"><label className="field">Analyst notes<textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={5} placeholder="Record evidence, limitations and review steps."/></label><label className="field">Disposition<textarea value={disposition} onChange={e=>setDisposition(e.target.value)} rows={5} placeholder="Required before closing; state the conclusion and remaining uncertainty."/></label></div>
      <div className="reviewAttach"><label className="field">Configuration review ID<input value={reviewId} onChange={e=>setReviewId(e.target.value)} placeholder="Persisted review reference"/></label><button className="ghost" type="button" disabled={busy||!reviewId.trim()} onClick={attach}>Attach review</button></div>
      <div className="linkedArtifacts"><span>Linked reviews</span>{(selected.payload.review_ids??[]).length?<div>{(selected.payload.review_ids??[]).map(id=><code key={id}>{id}</code>)}</div>:<b>None attached</b>}</div>
      {error?<p className="error" role="alert">{error}</p>:null}
      <div className="panelFooter artifactFooter"><span>Closing requires a recorded disposition; missing evidence remains explicit.</span><div className="toolbarActions"><button className="ghost" type="button" disabled={busy} onClick={()=>void update("in_review")}>{busy?"Saving…":"Save / mark in review"}</button><button className="button" type="button" disabled={busy||!disposition.trim()} onClick={()=>void update("closed")}>Close with disposition</button><a className="ghost" href={`/api/v1/protocol-investigations/${encodeURIComponent(selected.id)}/render?format=pdf`} target="_blank" rel="noopener noreferrer">Open PDF report</a></div></div>
    </section>:null}
  </>;
}
