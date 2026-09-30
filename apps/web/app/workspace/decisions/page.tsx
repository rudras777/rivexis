"use client";

import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {useEffect,useMemo,useRef,useState} from "react";
import {ApiError,api,apiBlob} from "@/lib/api";
import {useWorkspace,workspaceQueryKey} from "@/components/WorkspaceContext";

type HistoryRow={
  type:"analysis"|"decision"|string;
  id:string;
  workspace_id:string;
  engine_id?:string|null;
  demo?:boolean|null;
  created_at:string;
};
type Detail=Record<string,unknown>;
type ReportFormat="json"|"html"|"pdf";
type CreateDecisionVars={workspaceId:string;analysisIds:string[];epoch:number};

function message(error:unknown,kind:"history"|"decision"|"report"){
  if(error instanceof ApiError){
    if(error.status===401)return "Your session ended before Rivexis could complete this operation.";
    if(error.status===403)return "Your current workspace role does not permit this operation.";
    if(error.status===404)return kind==="history"?"Decision inputs are unavailable because workspace access could not be confirmed.":"One or more persisted decision records are no longer available in this workspace.";
    if(error.status===409)return "The selected persisted analyses cannot be combined into one decision boundary.";
    if(error.status===422)return "Rivexis rejected the decision/report request because the persisted inputs were not valid for this operation.";
    if(error.status===503)return "The decision/report service is temporarily unavailable.";
  }
  return kind==="report"?"Rivexis could not generate the persisted report.":kind==="decision"?"Rivexis could not create the canonical decision.":"Rivexis could not load decision inputs for this workspace.";
}

function recordedAt(value:string){
  const date=new Date(value);
  return Number.isNaN(date.getTime())?value:date.toLocaleString();
}
function text(value:unknown,fallback="—"){return typeof value==="string"&&value.trim()?value:fallback}
function numberText(value:unknown,suffix=""){return typeof value==="number"&&Number.isFinite(value)?`${value}${suffix}`:"—"}
function list(value:unknown){return Array.isArray(value)?value.filter((item):item is string=>typeof item==="string"&&Boolean(item.trim())):[]}
function record(value:unknown){return value&&typeof value==="object"&&!Array.isArray(value)?value as Record<string,unknown>:{} }

function download(blob:Blob,filename:string){
  const url=URL.createObjectURL(blob);
  const anchor=document.createElement("a");
  anchor.href=url;anchor.download=filename;anchor.style.display="none";
  document.body.appendChild(anchor);anchor.click();anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),0);
}

function DecisionDetail({decision}:{decision:Detail}){
  const statuses=record(decision.engine_statuses);
  const versions=record(decision.engine_versions);
  const frameworks=record(decision.analysis_framework_versions);
  const engines=[...new Set([...Object.keys(statuses),...Object.keys(versions),...Object.keys(frameworks)])].sort();
  const analysisIds=list(decision.analysis_ids);
  const sources=list(decision.evidence_sources);
  const why=list(decision.why);
  const missing=list(decision.missing_data);
  return <div data-testid="decision-desk-detail">
    {decision.demo===true?<div className="resultBanner isDemo" role="status"><span className="statusDot"/>DEMONSTRATION INPUT PRESENT — REPORT MUST REMAIN LABELLED SYNTHETIC</div>:null}
    <div className="resultHero"><div><span className="workspaceKicker">Canonical decision</span><strong>{text(decision.decision,"UNKNOWN")}</strong><p>{text(decision.executive_summary,"No executive summary was persisted.")}</p></div><div className="resultScore"><span>RISK SCORE</span><b>{numberText(decision.overall_risk_score)}</b><small>{typeof decision.overall_risk_score==="number"?"/100":""}</small></div></div>
    <div className="resultGrid">
      <div><span>Decision confidence</span><b>{numberText(decision.decision_confidence,"%")}</b></div>
      <div><span>Data confidence</span><b>{numberText(decision.data_confidence,"%")}</b></div>
      <div><span>Methodology</span><b>{text(decision.decision_methodology_version)}</b></div>
      <div><span>Canonical persistence</span><b>{decision.canonical_persistence_verified===true?"VERIFIED":"NOT VERIFIED"}</b></div>
      <div><span>Evidence records</span><b>{numberText(decision.evidence_count)}</b></div>
      <div><span>Evidence sources</span><b>{sources.join(", ")||"None recorded"}</b></div>
      <div><span>Unresolved conflicts</span><b>{numberText(decision.unresolved_conflict_count)}</b></div>
    </div>
    {why.length?<section className="findingBlock"><h3>Why</h3><ul>{why.map(item=><li key={item}>{item}</li>)}</ul></section>:null}
    {missing.length?<section className="findingBlock warning"><h3>Missing data</h3><ul>{missing.map(item=><li key={item}>{item}</li>)}</ul></section>:null}
    <h3>Specialist provenance</h3>
    {engines.length?<div className="tableWrap"><table className="table"><thead><tr><th>Engine</th><th>Status</th><th>Engine version</th><th>Framework</th></tr></thead><tbody>{engines.map(engine=><tr key={engine}><td>{engine}</td><td>{text(statuses[engine],"UNKNOWN")}</td><td>{text(versions[engine])}</td><td>{text(frameworks[engine])}</td></tr>)}</tbody></table></div>:<p className="muted">No specialist engine provenance is recorded.</p>}
    <h3>Persisted analysis references</h3>
    {analysisIds.length?<ul>{analysisIds.map(id=><li key={id}><code>{id}</code></li>)}</ul>:<p className="muted">No persisted analysis references are recorded.</p>}
    <div className="advancedOnly"><b>Recommended action</b><p>{text(decision.recommended_action,"No recommended action was persisted.")}</p></div>
  </div>;
}

export default function DecisionDesk(){
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const epochRef=useRef(0);
  const queryClient=useQueryClient();
  const [selectedIds,setSelectedIds]=useState<string[]>([]);
  const [decisionId,setDecisionId]=useState("");
  const [reporting,setReporting]=useState<ReportFormat|null>(null);
  const [decisionError,setDecisionError]=useState("");
  const [reportError,setReportError]=useState("");
  const [notice,setNotice]=useState("");

  useEffect(()=>{
    workspaceRef.current=workspaceId;
    epochRef.current+=1;
    setSelectedIds([]);
    setDecisionId("");
    setReporting(null);
    setDecisionError("");
    setReportError("");
    setNotice("");
  },[workspaceId]);

  const history=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"history"),
    queryFn:()=>api<{items:HistoryRow[]}>(`/api/v1/history?workspace_id=${encodeURIComponent(workspaceId)}`),
    retry:false,
  });
  const analyses=useMemo(()=>history.data?.items.filter(item=>item.type==="analysis")??[],[history.data?.items]);
  const decisions=useMemo(()=>history.data?.items.filter(item=>item.type==="decision")??[],[history.data?.items]);
  const selectedEngines=useMemo(()=>new Set(analyses.filter(item=>selectedIds.includes(item.id)).map(item=>item.engine_id).filter(Boolean)),[analyses,selectedIds]);

  const decision=useQuery({
    queryKey:workspaceQueryKey(workspaceId,"decision-desk",decisionId||"none"),
    queryFn:()=>api<Detail>(`/api/v1/decisions/${encodeURIComponent(decisionId)}`),
    enabled:Boolean(decisionId),retry:false,
  });

  const createDecision=useMutation({
    mutationFn:async(vars:CreateDecisionVars)=>{
      const details=await Promise.all(vars.analysisIds.map(id=>api<Detail>(`/api/v1/analyses/${encodeURIComponent(id)}`)));
      return api<Detail>("/api/v1/decisions/analyze",{method:"POST",body:JSON.stringify({engine_results:details})});
    },
    onSuccess:(result,vars)=>{
      void queryClient.invalidateQueries({queryKey:workspaceQueryKey(vars.workspaceId,"history")});
      if(workspaceRef.current!==vars.workspaceId||epochRef.current!==vars.epoch)return;
      const id=typeof result.decision_id==="string"?result.decision_id:"";
      if(id)setDecisionId(id);
      setDecisionError("");
      setNotice(id?`Persisted decision ${id} created from ${vars.analysisIds.length} canonical analysis reference${vars.analysisIds.length===1?"":"s"}.`:"Decision created.");
      setReportError("");
    },
    onError:(error,vars)=>{
      if(workspaceRef.current===vars.workspaceId&&epochRef.current===vars.epoch)setDecisionError(message(error,"decision"));
    },
  });

  function toggle(item:HistoryRow){
    setNotice("");setDecisionError("");setReportError("");
    setSelectedIds(current=>{
      if(current.includes(item.id))return current.filter(id=>id!==item.id);
      if(current.length>=10)return current;
      if(item.engine_id&&analyses.some(other=>current.includes(other.id)&&other.engine_id===item.engine_id))return current;
      return [...current,item.id];
    });
  }

  async function generate(format:ReportFormat){
    if(!decisionId||reporting)return;
    const originWorkspace=workspaceId;
    const originDecision=decisionId;
    const originEpoch=epochRef.current;
    setReporting(format);setReportError("");
    try{
      const blob=await apiBlob("/api/v1/reports",{method:"POST",body:JSON.stringify({decision_id:originDecision,format})});
      if(workspaceRef.current!==originWorkspace||epochRef.current!==originEpoch)return;
      download(blob,`rivexis-decision-${originDecision}.${format}`);
      setNotice(`Persisted ${format.toUpperCase()} report generated for decision ${originDecision}.`);
    }catch(error){
      if(workspaceRef.current===originWorkspace&&epochRef.current===originEpoch)setReportError(message(error,"report"));
    }finally{
      if(workspaceRef.current===originWorkspace&&epochRef.current===originEpoch)setReporting(null);
    }
  }

  const operationBusy=createDecision.isPending||Boolean(reporting);

  return <>
    <div className="workspaceHeader"><div><h1>Decision Desk</h1><p>Synthesize canonical persisted analyses into a decision, then generate a persisted evidence-grounded report.</p></div><span className="badge">{workspace.name}</span></div>

    <section className="modePanel" data-testid="decision-input-selector"><div><span className="workspaceKicker">Decision inputs</span><h2>Select persisted specialist analyses</h2><p>Rivexis accepts at most one recent result per specialist engine and at most 10 inputs. The backend rehydrates each reference from persistence before scoring.</p></div><div className="modeNotice live"><span className="statusDot"/>{selectedIds.length} / 10 selected · duplicate engine weighting is blocked in this interface.</div></section>

    <section className="panel">
      {history.isPending?<p>Loading persisted analyses for {workspace.name}…</p>:null}
      {history.isError?<p className="error" role="alert">{message(history.error,"history")}</p>:null}
      {!history.isPending&&!history.isError&&!analyses.length?<p>No persisted analyses are available yet. Run one or more specialist engines before creating a decision.</p>:null}
      {!history.isPending&&!history.isError&&analyses.length?<div className="tableWrap"><table className="table"><thead><tr><th>Use</th><th>Engine</th><th>Reference</th><th>Mode</th><th>Recorded</th></tr></thead><tbody>{analyses.map(item=>{
        const checked=selectedIds.includes(item.id);
        const duplicateEngine=Boolean(item.engine_id)&&selectedEngines.has(item.engine_id)&&!checked;
        const limitReached=selectedIds.length>=10&&!checked;
        return <tr key={item.id}><td><input type="checkbox" aria-label={`Select analysis ${item.id} for decision`} checked={checked} disabled={duplicateEngine||limitReached||operationBusy} onChange={()=>toggle(item)}/></td><td>{item.engine_id??"—"}</td><td><code>{item.id}</code></td><td>{item.demo===true?"Demo":"Non-demo"}</td><td>{recordedAt(item.created_at)}</td></tr>;
      })}</tbody></table></div>:null}
      <div className="runBar"><div><span>CANONICAL PERSISTED INPUTS</span><small>{selectedIds.length?`${selectedIds.length} reference${selectedIds.length===1?"":"s"} ready for server rehydration`:"Select at least one analysis"}</small></div><button className="button runButton" disabled={!selectedIds.length||operationBusy} onClick={()=>{setDecisionError("");setNotice("");createDecision.mutate({workspaceId,analysisIds:[...selectedIds],epoch:epochRef.current})}}>{createDecision.isPending?"Creating decision…":"Create canonical decision ↗"}</button></div>
      {decisionError?<p className="error" role="alert">{decisionError}</p>:null}
      {notice?<p className="success" role="status">{notice}</p>:null}
    </section>

    {decisions.length?<section className="panel"><div className="panelHeading"><div><span className="workspaceKicker">Decision history</span><h2>Persisted decisions</h2></div><span className="stepLabel">{decisions.length} RECENT</span></div><div className="tableWrap"><table className="table"><thead><tr><th>Reference</th><th>Recorded</th><th>Action</th></tr></thead><tbody>{decisions.map(item=><tr key={item.id}><td><code>{item.id}</code></td><td>{recordedAt(item.created_at)}</td><td><button className={decisionId===item.id?"button":"ghost"} disabled={operationBusy} onClick={()=>{setDecisionId(item.id);setReportError("");setNotice("")}}>{decisionId===item.id?"Selected":"Inspect"}</button></td></tr>)}</tbody></table></div></section>:null}

    {decisionId?<section className="panel" aria-live="polite" data-testid="decision-report-workbench"><div className="panelHeading"><div><span className="workspaceKicker">Decision provenance</span><h2>Persisted decision & reports</h2><p>Reports are created server-side from this persisted decision. JSON, HTML and PDF all record a report row before rendering.</p></div><span className="stepLabel">{decisionId}</span></div>
      {decision.isPending?<p>Loading canonical decision…</p>:null}
      {decision.isError?<p className="error" role="alert">{message(decision.error,"decision")}</p>:null}
      {decision.data?<><DecisionDetail decision={decision.data}/><div className="runBar"><div><span>PERSISTED REPORT OUTPUT</span><small>JSON · HTML · PDF</small></div><div className="actions"><button className="ghost" disabled={operationBusy} onClick={()=>void generate("json")}>{reporting==="json"?"Generating…":"Download JSON"}</button><button className="ghost" disabled={operationBusy} onClick={()=>void generate("html")}>{reporting==="html"?"Generating…":"Download HTML"}</button><button className="button" disabled={operationBusy} onClick={()=>void generate("pdf")}>{reporting==="pdf"?"Generating…":"Download PDF"}</button></div></div></>:null}
      {reportError?<p className="error" role="alert">{reportError}</p>:null}
    </section>:null}
  </>;
}
