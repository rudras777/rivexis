"use client";

import {useEffect,useRef,useState} from "react";
import {api} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

type Mode="timeline"|"compare";
type EventRow={event:string;category:string;source_role:string;block_number?:number;block_datetime?:string;transaction_hash?:string;parameters?:Record<string,unknown>};
type ChangeRow={path:string;from:unknown;to:unknown;materiality:"HIGH"|"MEDIUM"|"LOW"};
type Result={event_count?:number;change_count?:number;materiality_counts?:Record<string,number>;events?:EventRow[];changes?:ChangeRow[];deployment_identity?:Record<string,unknown>;log_fetch?:Record<string,unknown>;[key:string]:unknown};
type Review={id:string;status:string;approved_at?:string|null};

function short(value:unknown){const s=String(value??"—");return s.length>34?`${s.slice(0,16)}…${s.slice(-12)}`:s}
function isBlock(value:string){return /^(0|[1-9]\d{0,15})$/.test(value)&&BigInt(value)<=BigInt(Number.MAX_SAFE_INTEGER)}
function validRange(from:string,to:string){return isBlock(from)&&isBlock(to)&&BigInt(from)<=BigInt(to)}
function isEvmAddress(value:string){return /^0x[a-fA-F0-9]{40}$/.test(value)}
function isBytes32(value:string){return /^0x[a-fA-F0-9]{64}$/.test(value)}

export default function ProtocolHistoryPage(){
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const epochRef=useRef(0);
  const [adapter,setAdapter]=useState("aave_v3");
  const [chain,setChain]=useState("ethereum");
  const [fromBlock,setFromBlock]=useState("");
  const [toBlock,setToBlock]=useState("");
  const [subject,setSubject]=useState("");
  const [market,setMarket]=useState("usdc");
  const [timestamps,setTimestamps]=useState(true);
  const [result,setResult]=useState<Result|null>(null);
  const [mode,setMode]=useState<Mode|null>(null);
  const [review,setReview]=useState<Review|null>(null);
  const [error,setError]=useState("");
  const [running,setRunning]=useState<string|null>(null);

  useEffect(()=>{
    workspaceRef.current=workspaceId;
    epochRef.current+=1;
    setResult(null);setMode(null);setReview(null);setError("");setRunning(null);
  },[workspaceId]);

  function changeAdapter(next:string){setAdapter(next);setSubject("");setResult(null);setMode(null);setReview(null);setError("")}
  function input(){
    const x:Record<string,unknown>={protocol_adapter:adapter,chain,from_block:fromBlock,to_block:toBlock};
    if(adapter==="aave_v3"&&subject)x.asset_address=subject;
    if(adapter==="compound_v3"){if(subject)x.collateral_asset=subject;x.compound_market=market||"usdc"}
    if(adapter==="morpho_blue"&&subject)x.morpho_market_id=subject;
    if(timestamps)x.hydrate_timestamps=true;
    return x;
  }

  async function run(next:Mode){
    const originWorkspace=workspaceId;const epoch=epochRef.current;
    setRunning(next);setError("");setResult(null);setReview(null);
    try{
      const path=next==="timeline"?"/api/v1/protocol-history/timeline":"/api/v1/protocol-config/compare";
      const data=await api<Result>(path,{method:"POST",body:JSON.stringify({workspace_id:originWorkspace,input:input()})});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==epoch)return;
      setResult(data);setMode(next);
    }catch{
      if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not complete this protocol-history read. Review provider availability and input, then retry.");
    }finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setRunning(null)}
  }

  async function saveReview(){
    const originWorkspace=workspaceId;const epoch=epochRef.current;
    setRunning("save");setError("");
    try{
      const row=await api<Review>("/api/v1/protocol-config/reviews",{method:"POST",body:JSON.stringify({workspace_id:originWorkspace,input:input()})});
      if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setReview(row);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not save this configuration review.")}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setRunning(null)}
  }

  async function approveReview(){
    if(!review)return;const originWorkspace=workspaceId;const epoch=epochRef.current;const reviewId=review.id;
    setRunning("approve");setError("");
    try{
      const row=await api<Review>(`/api/v1/protocol-config/reviews/${encodeURIComponent(reviewId)}/approve`,{method:"POST"});
      if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setReview(row);
    }catch{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setError("Rivexis could not approve this review.")}
    finally{if(workspaceRef.current===originWorkspace&&epochRef.current===epoch)setRunning(null)}
  }

  const rangeValid=validRange(fromBlock,toBlock);
  const subjectValid=!subject||(adapter==="morpho_blue"?isBytes32(subject):isEvmAddress(subject));
  const formValid=rangeValid&&subjectValid;
  const subjectLabel=adapter==="morpho_blue"?"Market ID (bytes32)":adapter==="compound_v3"?"Collateral asset":"Reserve asset";
  const events=result?.events??[];const changes=result?.changes??[];
  const high=Number(result?.materiality_counts?.HIGH??0);
  const medium=Number(result?.materiality_counts?.MEDIUM??0);

  return <>
    <div className="workspaceHeader dashboardHeader"><div><div className="workspaceKicker">Protocol evidence workflow</div><h1>Protocol history</h1><p>Read normalized events, compare archive-block configuration and preserve review artifacts.</p></div><div className="workspaceHeaderActions"><span className="badge"><span className="statusDot"/>{workspace.name}</span><span className="badge">ARCHIVE EVIDENCE</span></div></div>
    <section className="overviewBand surfaceOverview" aria-label="Protocol history overview"><div><small>MODE</small><strong>{mode?mode==="timeline"?"EVT":"CFG":"—"}</strong><span>{mode?mode==="timeline"?"Event timeline":"Configuration comparison":"Awaiting analysis"}</span></div><div><small>EVENTS</small><strong>{result?result.event_count??0:"—"}</strong><span>Normalized supported events</span></div><div><small>CHANGES</small><strong>{result?result.change_count??0:"—"}</strong><span>{result?`${high} high · ${medium} medium`:"No comparison yet"}</span></div><div><small>REVIEW</small><strong>{review?review.status.toUpperCase():"—"}</strong><span>{review?"Persisted workspace artifact":"Not saved"}</span></div></section>
    <div className="truthNotice"><span className="statusDot"/>An empty event set is not proof that no governance activity occurred. Provider availability, bounded coverage and missing evidence remain explicit.</div>
    <section className="panel operationalPanel">
      <div className="panelHeading"><div><span className="workspaceKicker">Bounded query</span><h2>Evidence parameters</h2></div><p className="sectionLead">Block values must be canonical non-negative decimals and the end block cannot precede the start block.</p></div>
      <div className="protocolFormGrid">
        <label className="field">Protocol<select value={adapter} onChange={e=>changeAdapter(e.target.value)}><option value="aave_v3">Aave V3</option><option value="compound_v3">Compound III</option><option value="morpho_blue">Morpho Blue</option></select></label>
        <label className="field">Network<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label>
        <label className="field">From block<input inputMode="numeric" aria-invalid={fromBlock.length>0&&!isBlock(fromBlock)} value={fromBlock} onChange={e=>setFromBlock(e.target.value)} placeholder="e.g. 21000000"/></label>
        <label className="field">To block<input inputMode="numeric" aria-invalid={toBlock.length>0&&!isBlock(toBlock)} value={toBlock} onChange={e=>setToBlock(e.target.value)} placeholder="e.g. 21010000"/></label>
        <label className="field">{subjectLabel}<input aria-invalid={subject.length>0&&!subjectValid} value={subject} onChange={e=>setSubject(e.target.value.trim())} placeholder={adapter==="morpho_blue"?"Optional 0x + 64 hex":"Optional 0x + 40 hex"}/></label>
        {adapter==="compound_v3"?<label className="field">Market<select value={market} onChange={e=>setMarket(e.target.value)}><option value="usdc">USDC</option></select></label>:null}
      </div>
      {(fromBlock||toBlock)&&!rangeValid?<p className="fieldError" role="status">Enter a complete block range with the from block less than or equal to the to block.</p>:null}
      {subject&&!subjectValid?<p className="fieldError" role="status">Enter the complete hexadecimal identity required by the selected protocol adapter.</p>:null}
      <label className="checkField"><input type="checkbox" checked={timestamps} onChange={e=>setTimestamps(e.target.checked)}/><span><b>Hydrate block timestamps</b><small>Uses bounded provider reads when that capability is available.</small></span></label>
      <div className="actionBar"><div><span>QUERY READINESS</span><small>{formValid?"Validated range ready for an attributed read":"Complete a valid range before execution"}</small></div><div className="toolbarActions"><button className="ghost" type="button" disabled={!!running||!formValid} onClick={()=>void run("timeline")}>{running==="timeline"?"Reading events…":"Read event timeline"}</button><button className="button" type="button" disabled={!!running||!formValid} onClick={()=>void run("compare")}>{running==="compare"?"Comparing…":"Compare configuration"}</button></div></div>
      {error?<p className="error" role="alert">{error}</p>:null}
    </section>

    {result?<section className="panel resultPanel" data-testid="protocol-history-result">
      <div className="resultBanner isLive" role="status"><span className="statusDot"/>{mode==="timeline"?"NORMALIZED EVENT EVIDENCE":"CONFIGURATION COMPARISON"} · {workspace.name}</div>
      <div className="artifactMetrics"><div><span>Normalized events</span><b>{result.event_count??0}</b></div><div><span>Configuration changes</span><b>{result.change_count??0}</b></div><div><span>High materiality</span><b>{high}</b></div><div><span>Medium materiality</span><b>{medium}</b></div></div>
      {mode==="timeline"?<div className="tableWrap"><table className="table"><thead><tr><th>Block / time</th><th>Event</th><th>Category</th><th>Source</th><th>Parameters</th><th>Transaction</th></tr></thead><tbody>{events.length?events.map((event,index)=><tr key={`${event.transaction_hash}-${index}`}><td>{event.block_number??"—"}<br/><small>{event.block_datetime??"Timestamp unavailable"}</small></td><td><b>{event.event}</b></td><td><span className="statePill neutral">{event.category}</span></td><td>{event.source_role}</td><td><code>{short(JSON.stringify(event.parameters))}</code></td><td><code title={event.transaction_hash}>{short(event.transaction_hash)}</code></td></tr>):<tr><td colSpan={6}>No supported events were returned in this bounded range. This is not proof that no governance activity occurred.</td></tr>}</tbody></table></div>:null}
      {mode==="compare"?<><div className="tableWrap"><table className="table"><thead><tr><th>Materiality</th><th>Configuration path</th><th>Before</th><th>After</th></tr></thead><tbody>{changes.length?changes.map((change,index)=><tr key={`${change.path}-${index}`}><td><span className={`statePill ${change.materiality==="HIGH"?"warning":"neutral"}`}>{change.materiality}</span></td><td><code>{change.path}</code></td><td><code>{short(change.from)}</code></td><td><code>{short(change.to)}</code></td></tr>):<tr><td colSpan={4}>No configuration changes were detected between the selected blocks.</td></tr>}</tbody></table></div><div className="panelFooter"><span>Persist the exact comparison before approval or case attachment.</span><button className="button" type="button" disabled={!!running} onClick={saveReview}>{running==="save"?"Saving…":"Save review artifact"}</button></div></>:null}
      <details className="advancedPayload"><summary>Inspect normalized evidence payload</summary><pre className="result">{JSON.stringify(result,null,2)}</pre></details>
    </section>:null}

    {review?<section className="panel artifactCard" data-testid="protocol-review"><div><span className="workspaceKicker">Persisted configuration review</span><h2>Review <code>{review.id}</code></h2><p>Approval records analyst workflow; it does not certify protocol safety or complete provider coverage.</p></div><div className="artifactActions"><span className={`statePill ${review.status.toLowerCase()==="approved"?"positive":"neutral"}`}>{review.status}</span>{review.status.toLowerCase()!=="approved"?<button className="button" type="button" disabled={!!running} onClick={approveReview}>{running==="approve"?"Approving…":"Approve review"}</button>:null}<a className="ghost" href={`/api/v1/protocol-config/reviews/${encodeURIComponent(review.id)}/render?format=pdf`} target="_blank" rel="noopener noreferrer">Open PDF report</a></div></section>:null}
  </>;
}
