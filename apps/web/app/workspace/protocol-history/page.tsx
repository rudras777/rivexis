"use client";

import {useState} from "react";
import {activeWorkspaceId,api,apiBlob} from "@/lib/api";

type Mode="timeline"|"compare";
type EventRow={event:string;category:string;source_role:string;block_number?:number;block_datetime?:string;transaction_hash?:string;parameters?:Record<string,unknown>};
type ChangeRow={path:string;from:unknown;to:unknown;materiality:"HIGH"|"MEDIUM"|"LOW"};
type Result={event_count?:number;change_count?:number;materiality_counts?:Record<string,number>;events?:EventRow[];changes?:ChangeRow[];deployment_identity?:Record<string,unknown>;log_fetch?:Record<string,unknown>;[key:string]:unknown};
type Review={id:string;status:string;approved_at?:string|null};

function short(value:unknown){const s=String(value??"—");return s.length>34?`${s.slice(0,16)}…${s.slice(-12)}`:s}
export default function ProtocolHistoryPage(){
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

  function input(){
    const x:Record<string,unknown>={protocol_adapter:adapter,chain,from_block:fromBlock,to_block:toBlock};
    if(adapter==="aave_v3"&&subject)x.asset_address=subject;
    if(adapter==="compound_v3"){if(subject)x.collateral_asset=subject;x.compound_market=market||"usdc"}
    if(adapter==="morpho_blue"&&subject)x.morpho_market_id=subject;
    if(timestamps)x.hydrate_timestamps=true;
    return x;
  }
  function workspace(){const id=activeWorkspaceId();if(!id)throw new Error("No active workspace selected");return id}
  async function run(next:Mode){
    setRunning(next);setError("");setResult(null);setReview(null);
    try{
      const path=next==="timeline"?"/api/v1/protocol-history/timeline":"/api/v1/protocol-config/compare";
      const data=await api<Result>(path,{method:"POST",body:JSON.stringify({workspace_id:workspace(),input:input()})});
      setResult(data);setMode(next);
    }catch(e){setError((e as Error).message)}finally{setRunning(null)}
  }
  async function saveReview(){
    setRunning("save");setError("");
    try{const row=await api<Review>("/api/v1/protocol-config/reviews",{method:"POST",body:JSON.stringify({workspace_id:workspace(),input:input()})});setReview(row)}
    catch(e){setError((e as Error).message)}finally{setRunning(null)}
  }
  async function approveReview(){
    if(!review)return;setRunning("approve");setError("");
    try{setReview(await api<Review>(`/api/v1/protocol-config/reviews/${review.id}/approve`,{method:"POST"}))}
    catch(e){setError((e as Error).message)}finally{setRunning(null)}
  }
  async function openPdf(){
    if(!review)return;setRunning("pdf");setError("");
    try{const blob=await apiBlob(`/api/v1/protocol-config/reviews/${review.id}/render?format=pdf`);const url=URL.createObjectURL(blob);window.open(url,"_blank","noopener,noreferrer");setTimeout(()=>URL.revokeObjectURL(url),60000)}
    catch(e){setError((e as Error).message)}finally{setRunning(null)}
  }
  const subjectLabel=adapter==="morpho_blue"?"Market ID (bytes32)":adapter==="compound_v3"?"Collateral asset":"Reserve asset";
  const events=result?.events??[];const changes=result?.changes??[];
  return <>
    <div className="workspaceHeader"><div><h1>Protocol History</h1><p>Read normalized governance/configuration events, compare protocol-native state between archive blocks, and preserve configuration changes as review artifacts.</p></div></div>
    <section className="panel">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:14}}>
        <label className="field">Protocol<select value={adapter} onChange={e=>setAdapter(e.target.value)}><option value="aave_v3">Aave V3</option><option value="compound_v3">Compound III</option><option value="morpho_blue">Morpho Blue</option></select></label>
        <label className="field">Chain<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label>
        <label className="field">From block<input value={fromBlock} onChange={e=>setFromBlock(e.target.value)} placeholder="e.g. 21000000"/></label>
        <label className="field">To block<input value={toBlock} onChange={e=>setToBlock(e.target.value)} placeholder="e.g. 21010000"/></label>
        <label className="field">{subjectLabel}<input value={subject} onChange={e=>setSubject(e.target.value)} placeholder={adapter==="morpho_blue"?"0x…64 hex chars":"0x…address"}/></label>
        {adapter==="compound_v3"?<label className="field">Market<select value={market} onChange={e=>setMarket(e.target.value)}><option value="usdc">USDC</option></select></label>:null}
      </div>
      <label style={{display:"flex",gap:8,alignItems:"center",marginTop:12,fontSize:13}}><input type="checkbox" checked={timestamps} onChange={e=>setTimestamps(e.target.checked)}/> Hydrate event block timestamps (bounded RPC reads)</label>
      <div style={{display:"flex",gap:10,marginTop:16,flexWrap:"wrap"}}><button className="button" disabled={!!running} onClick={()=>run("timeline")}>{running==="timeline"?"Reading events…":"Read event timeline"}</button><button className="button" disabled={!!running} onClick={()=>run("compare")}>{running==="compare"?"Comparing…":"Compare configuration"}</button>{mode==="compare"&&result?<button className="button" disabled={!!running} onClick={saveReview}>{running==="save"?"Saving…":"Save review artifact"}</button>:null}</div>
      {error?<p className="error">{error}</p>:null}
      {review?<div style={{marginTop:14}}><b>Review {review.id}</b> · {review.status} {review.status!=="approved"?<button className="button" style={{marginLeft:10}} disabled={!!running} onClick={approveReview}>Approve review</button>:null}<button className="button" style={{marginLeft:10}} disabled={!!running} onClick={openPdf}>{running==="pdf"?"Rendering…":"Open PDF report"}</button></div>:null}
    </section>
    {result?<section className="panel">
      <div style={{display:"flex",gap:24,flexWrap:"wrap",marginBottom:16}}><div><b>{result.event_count??"—"}</b><div>normalized events</div></div><div><b>{result.change_count??"—"}</b><div>configuration changes</div></div>{result.materiality_counts?<><div><b>{String(result.materiality_counts.HIGH??0)}</b><div>high</div></div><div><b>{String(result.materiality_counts.MEDIUM??0)}</b><div>medium</div></div></>:null}</div>
      {mode==="timeline"?<div style={{overflowX:"auto"}}><table><thead><tr><th>Block / time</th><th>Event</th><th>Category</th><th>Source</th><th>Parameters</th><th>Tx</th></tr></thead><tbody>{events.length?events.map((e,i)=><tr key={`${e.transaction_hash}-${i}`}><td>{e.block_number??"—"}<br/><small>{e.block_datetime??"timestamp not hydrated"}</small></td><td><b>{e.event}</b></td><td>{e.category}</td><td>{e.source_role}</td><td><code>{JSON.stringify(e.parameters)}</code></td><td><code title={e.transaction_hash}>{short(e.transaction_hash)}</code></td></tr>):<tr><td colSpan={6}>No supported events found in this range. This is not proof that no governance activity occurred.</td></tr>}</tbody></table></div>:null}
      {mode==="compare"?<div style={{overflowX:"auto"}}><table><thead><tr><th>Priority</th><th>Configuration path</th><th>Before</th><th>After</th></tr></thead><tbody>{changes.length?changes.map((c,i)=><tr key={`${c.path}-${i}`}><td><b>{c.materiality}</b></td><td><code>{c.path}</code></td><td><code>{short(c.from)}</code></td><td><code>{short(c.to)}</code></td></tr>):<tr><td colSpan={4}>No configuration changes detected between the selected blocks.</td></tr>}</tbody></table></div>:null}
      <details style={{marginTop:16}}><summary>Raw evidence payload</summary><pre style={{whiteSpace:"pre-wrap",wordBreak:"break-word",fontSize:12,maxHeight:420,overflow:"auto"}}>{JSON.stringify(result,null,2)}</pre></details>
    </section>:null}
  </>;
}
