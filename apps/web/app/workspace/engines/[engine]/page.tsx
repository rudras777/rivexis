"use client";

import {useParams} from "next/navigation";
import {useEffect,useMemo,useRef,useState} from "react";
import {api,enginePath,EngineId} from "@/lib/api";
import {useWorkspace} from "@/components/WorkspaceContext";

const demoDefaults:Record<EngineId,object>={
  B1:{will_revert:false,unlimited_approval:true},B2:{unlimited_approval:true},B3:{active_exploit:true},B4:{label_conflict:true},B5:{route_risk:48,low_liquidity:true},F1:{largest_exposure_pct:62},F2:{admin_privilege:true,oracle_risk:true},F3:{health_factor:1.12},F4:{apy:42,incentive_dependent:true},F5:{largest_allocation_pct:72,stablecoin_depeg_scenario_loss_pct:25}
};

const liveDefaults:Partial<Record<EngineId,object>>={
  B1:{chain:"ethereum",from:"0x1111111111111111111111111111111111111111",to:"0x2222222222222222222222222222222222222222",value:"0x0",data:"0x"},
  B2:{chain:"ethereum",to:"0x2222222222222222222222222222222222222222",data:"0x"},
  B3:{chain:"ethereum",entity:"0x1111111111111111111111111111111111111111",balance_change_threshold_pct:20,supply_change_threshold_pct:5,oracle_change_threshold_pct:10,oracle_max_age_seconds:3600},
  B4:{chain:"ethereum",wallet:"0x1111111111111111111111111111111111111111"},
  B5:{source_chain:"ethereum",destination_chain:"arbitrum",source_token:"USDC",destination_token:"USDC",amount:"1000000",wallet:"0x1111111111111111111111111111111111111111",slippage:0.005},
  F1:{manual_positions:[{coingecko_id:"ethereum",symbol:"ETH",quantity:1},{coingecko_id:"bitcoin",symbol:"BTC",quantity:0.05}]},
  F2:{protocol:"aave"},
  F3:{chain:"ethereum",collateral_price_feed:"",collateral_units:1,debt_units:1800,debt_price_usd:1,liquidation_threshold:0.8,collateral_coingecko_id:"ethereum"},
  F4:{protocol:"aave",asset:"USDC",chain:"Ethereum"},
  F5:{capital_usd:1000000,max_concentration_pct:35,market_shock_pct:30,stablecoin_depeg_pct:10,allocations:[{coingecko_id:"bitcoin",symbol:"BTC",weight_pct:30,stablecoin:false},{coingecko_id:"ethereum",symbol:"ETH",weight_pct:25,stablecoin:false},{coingecko_id:"usd-coin",symbol:"USDC",weight_pct:45,stablecoin:true}]}
};

const engineMeta:Record<EngineId,{name:string;domain:string;description:string}>={
  B1:{name:"Transaction Simulation",domain:"Blockchain · Execution",description:"Inspect execution intent, approvals, transfers and expected state changes before commitment."},
  B2:{name:"Transaction & Contract Security",domain:"Blockchain · Security",description:"Evaluate deterministic approval, bytecode, proxy and contract-control risk signals."},
  B3:{name:"Threat & Monitoring",domain:"Blockchain · Monitoring",description:"Detect material change across on-chain balances, supply state and oracle evidence."},
  B4:{name:"Entity & Fund Flow",domain:"Blockchain · Entities",description:"Review wallet state, counterparty context and attribution conflicts without inventing identity."},
  B5:{name:"Cross-Chain Route",domain:"Blockchain · Routing",description:"Compare route safety, liquidity, dependencies and execution complexity."},
  F1:{name:"Portfolio & Exposure",domain:"Finance · Portfolio",description:"Measure concentration, liquidity, valuation quality and portfolio risk contribution."},
  F2:{name:"Protocol Risk",domain:"Finance · Protocols",description:"Screen protocol, oracle, governance, economic and dependency risk."},
  F3:{name:"Position & Liquidation",domain:"Finance · Positions",description:"Evaluate health factor, liquidation distance and market-shock sensitivity."},
  F4:{name:"Yield & Strategy Risk",domain:"Finance · Yield",description:"Separate headline yield from sustainable, evidence-backed risk-adjusted return."},
  F5:{name:"Treasury Allocation & Scenario",domain:"Finance · Treasury",description:"Stress allocation, concentration, stablecoin and market-loss scenarios."},
};

type GuidedField={key:string;label:string;hint:string;type:"boolean"|"number"|"text"|"select";min?:number;max?:number;step?:number;options?:string[]};
type FieldSet={demo:GuidedField[];live:GuidedField[]};

const guidedFields:Record<EngineId,FieldSet>={
  B1:{demo:[
    {key:"will_revert",label:"Transaction reverts",hint:"Model a failed execution path.",type:"boolean"},
    {key:"unlimited_approval",label:"Unlimited token approval",hint:"Flag an unbounded allowance request.",type:"boolean"},
  ],live:[
    {key:"chain",label:"Network",hint:"Execution network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"from",label:"Sender address",hint:"Originating EVM account.",type:"text"},
    {key:"to",label:"Target address",hint:"Transaction destination.",type:"text"},
  ]},
  B2:{demo:[{key:"unlimited_approval",label:"Unlimited approval",hint:"Exercise deterministic approval-risk controls.",type:"boolean"}],live:[
    {key:"chain",label:"Network",hint:"Contract network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"to",label:"Contract address",hint:"Contract or transaction target.",type:"text"},
  ]},
  B3:{demo:[{key:"active_exploit",label:"Active exploit signal",hint:"Model a material active-threat condition.",type:"boolean"}],live:[
    {key:"chain",label:"Network",hint:"Monitoring network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"entity",label:"Entity address",hint:"Wallet or contract to monitor.",type:"text"},
    {key:"balance_change_threshold_pct",label:"Balance change threshold",hint:"Percent change that becomes material.",type:"number",min:0,max:100,step:1},
  ]},
  B4:{demo:[{key:"label_conflict",label:"Conflicting identity labels",hint:"Preserve unresolved attribution disagreement.",type:"boolean"}],live:[
    {key:"chain",label:"Network",hint:"Wallet network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"wallet",label:"Wallet address",hint:"Entity to investigate.",type:"text"},
  ]},
  B5:{demo:[
    {key:"route_risk",label:"Route risk score",hint:"Synthetic route risk from 0 to 100.",type:"number",min:0,max:100,step:1},
    {key:"low_liquidity",label:"Low liquidity",hint:"Model insufficient route depth.",type:"boolean"},
  ],live:[
    {key:"source_chain",label:"Source network",hint:"Origin network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"destination_chain",label:"Destination network",hint:"Destination network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"source_token",label:"Source asset",hint:"Source token symbol.",type:"text"},
    {key:"destination_token",label:"Destination asset",hint:"Destination token symbol.",type:"text"},
  ]},
  F1:{demo:[{key:"largest_exposure_pct",label:"Largest exposure",hint:"Largest position as a percent of portfolio.",type:"number",min:0,max:100,step:1}],live:[]},
  F2:{demo:[
    {key:"admin_privilege",label:"Material admin privilege",hint:"Model elevated protocol control.",type:"boolean"},
    {key:"oracle_risk",label:"Oracle dependency risk",hint:"Model a fragile oracle dependency.",type:"boolean"},
  ],live:[{key:"protocol",label:"Protocol slug",hint:"DefiLlama protocol identifier.",type:"text"}]},
  F3:{demo:[{key:"health_factor",label:"Health factor",hint:"Position health before liquidation.",type:"number",min:0,step:.01}],live:[
    {key:"chain",label:"Network",hint:"Position network.",type:"select",options:["ethereum","arbitrum","optimism","base"]},
    {key:"collateral_units",label:"Collateral units",hint:"Units of supplied collateral.",type:"number",min:0,step:.01},
    {key:"debt_units",label:"Debt units",hint:"Outstanding borrowed units.",type:"number",min:0,step:.01},
    {key:"liquidation_threshold",label:"Liquidation threshold",hint:"Protocol threshold from 0 to 1.",type:"number",min:0,max:1,step:.01},
  ]},
  F4:{demo:[
    {key:"apy",label:"Headline APY",hint:"Synthetic advertised annual yield.",type:"number",min:0,step:.1},
    {key:"incentive_dependent",label:"Incentive dependent",hint:"Model yield reliant on token incentives.",type:"boolean"},
  ],live:[
    {key:"protocol",label:"Protocol",hint:"Protocol name or slug.",type:"text"},
    {key:"asset",label:"Asset",hint:"Yield-bearing asset.",type:"text"},
    {key:"chain",label:"Network",hint:"Pool network.",type:"text"},
  ]},
  F5:{demo:[
    {key:"largest_allocation_pct",label:"Largest allocation",hint:"Largest treasury allocation percent.",type:"number",min:0,max:100,step:1},
    {key:"stablecoin_depeg_scenario_loss_pct",label:"Depeg scenario loss",hint:"Synthetic loss under a stablecoin depeg.",type:"number",min:0,max:100,step:1},
  ],live:[
    {key:"capital_usd",label:"Capital",hint:"Total treasury capital in USD.",type:"number",min:0,step:1000},
    {key:"max_concentration_pct",label:"Concentration limit",hint:"Maximum acceptable asset concentration.",type:"number",min:0,max:100,step:1},
    {key:"market_shock_pct",label:"Market shock",hint:"Downside market scenario percent.",type:"number",min:0,max:100,step:1},
  ]},
};

function stringValue(value:unknown,fallback="—"){
  return typeof value==="string"&&value.trim()?value:fallback;
}

function numberValue(value:unknown){
  return typeof value==="number"&&Number.isFinite(value)?value:null;
}

function stringList(value:unknown){
  return Array.isArray(value)?value.filter((item):item is string=>typeof item==="string"&&Boolean(item.trim())):[];
}

function evidenceProviders(value:unknown){
  if(!Array.isArray(value))return [];
  return [...new Set(value.map(item=>item&&typeof item==="object"&&"provider" in item?(item as {provider?:unknown}).provider:null).filter((provider):provider is string=>typeof provider==="string"&&Boolean(provider.trim())))].sort();
}

function conflictCount(value:unknown){
  return Array.isArray(value)?value.length:0;
}

function collectionRows(value:unknown){
  if(!Array.isArray(value))return [] as Record<string,unknown>[];
  return value.filter((item):item is Record<string,unknown>=>Boolean(item)&&typeof item==="object"&&!Array.isArray(item)).slice(0,50);
}

function ResultSummary({result}:{result:Record<string,unknown>}){
  const demo=result.demo===true;
  const status=stringValue(result.status,"UNKNOWN");
  const evidence=Array.isArray(result.evidence)?result.evidence:[];
  const providers=evidenceProviders(result.evidence);
  const conflicts=conflictCount(result.provider_conflicts);
  const missing=stringList(result.missing_data);
  const blockers=stringList(result.hard_blockers);
  const warnings=stringList(result.warnings);
  const assumptions=stringList(result.assumptions);
  const risk=numberValue(result.risk_score);
  const dataConfidence=numberValue(result.data_confidence);
  const engineConfidence=numberValue(result.engine_confidence);
  const providerConsensus=stringValue(result.provider_consensus,"UNAVAILABLE");
  const hasProviderEvidence=evidence.length>0;
  let banner="NO PROVIDER EVIDENCE RECORDED";
  if(demo)banner="DEMONSTRATION RESULT — NOT LIVE DATA";
  else if(status==="PROVIDER_UNAVAILABLE")banner="PROVIDER UNAVAILABLE — NO DECISION-GRADE PROVIDER RESULT";
  else if(status==="CONFLICTING_DATA")banner="CONFLICTING EVIDENCE — REVIEW BEFORE ACTING";
  else if(status==="STALE_DATA")banner="STALE EVIDENCE — REFRESH BEFORE ACTING";
  else if(status==="PARTIAL")banner="PARTIAL EVIDENCE — ANALYSIS IS INCOMPLETE";
  else if(hasProviderEvidence)banner=`${status} — ${evidence.length} RECORDED EVIDENCE ITEM${evidence.length===1?"":"S"}`;
  else banner=`${status} — NO PROVIDER EVIDENCE RECORDED`;

  const rows=[
    ["Status",status],
    ["Risk score",risk===null?"—":`${risk}/100`],
    ["Severity",stringValue(result.severity,"unknown")],
    ["Data confidence",dataConfidence===null?"—":`${dataConfidence}%`],
    ["Engine confidence",engineConfidence===null?"—":`${engineConfidence}%`],
    ["Engine version",stringValue(result.engine_version)],
    ["Analysis framework",stringValue(result.analysis_framework_version)],
    ["Provider consensus",providerConsensus],
    ["Evidence records",String(evidence.length)],
    ["Evidence sources",providers.length?providers.join(", "):"None recorded"],
    ["Unresolved source conflicts",String(conflicts)],
  ];

  return <div className="resultSummary" data-testid="engine-result-summary">
    <div className={`resultBanner ${demo?"isDemo":"isLive"}`} role="status"><span className="statusDot"/>{banner}</div>
    <div className="resultHero"><div><span className="workspaceKicker">Normalized outcome</span><strong>{status}</strong><p>{stringValue(result.summary,"No summary was returned.")}</p></div><div className="resultScore"><span>RISK SCORE</span><b>{risk===null?"—":risk}</b><small>{risk===null?"":"/100"}</small></div></div>
    <div className="resultGrid">{rows.slice(2).map(([label,value])=><div key={label}><span>{label}</span><b>{value}</b></div>)}</div>
    {(blockers.length>0||warnings.length>0||missing.length>0||assumptions.length>0)&&<div className="findingGrid">
      {blockers.length>0&&<section className="findingBlock critical"><h3>Hard blockers</h3><ul>{blockers.map(item=><li key={item}>{item}</li>)}</ul></section>}
      {warnings.length>0&&<section className="findingBlock warning"><h3>Warnings</h3><ul>{warnings.map(item=><li key={item}>{item}</li>)}</ul></section>}
      {missing.length>0&&<section className="findingBlock"><h3>Missing data</h3><ul>{missing.map(item=><li key={item}>{item}</li>)}</ul></section>}
      {assumptions.length>0&&<section className="findingBlock"><h3>Assumptions</h3><ul>{assumptions.map(item=><li key={item}>{item}</li>)}</ul></section>}
    </div>}
    <details className="advancedPayload"><summary>Inspect normalized JSON</summary><pre className="result">{JSON.stringify(result,null,2)}</pre></details>
  </div>;
}

export default function Engine(){
  const id=(useParams().engine as string).toUpperCase() as EngineId;
  const {workspaceId,workspace}=useWorkspace();
  const workspaceRef=useRef(workspaceId);
  const liveEnabled=["B1","B2","B3","B4","B5","F1","F2","F3","F4","F5"].includes(id);
  const [mode,setMode]=useState<"demo"|"live">("demo");
  const initial=useMemo(()=>JSON.stringify(demoDefaults[id]??{},null,2),[id]);
  const [text,setText]=useState(initial);
  const [result,setResult]=useState<Record<string,unknown>|null>(null);
  const [error,setError]=useState("");
  const [running,setRunning]=useState(false);
  const meta=engineMeta[id]??{name:`${id} Engine`,domain:"Specialist engine",description:"Run a normalized Rivexis analysis."};
  const fields=(guidedFields[id]?.[mode]??[]);
  const payload=useMemo(()=>{try{const value=JSON.parse(text);return value&&typeof value==="object"&&!Array.isArray(value)?value as Record<string,unknown>:null}catch{return null}},[text]);
  const portfolioPositions=id==="F1"&&mode==="live"?collectionRows(payload?.manual_positions):[];
  const treasuryAllocations=id==="F5"&&mode==="live"?collectionRows(payload?.allocations):[];
  const treasuryWeightTotal=treasuryAllocations.reduce((sum,allocation)=>sum+(typeof allocation.weight_pct==="number"&&Number.isFinite(allocation.weight_pct)?allocation.weight_pct:0),0);

  useEffect(()=>{
    workspaceRef.current=workspaceId;
    setResult(null);
    setError("");
    setRunning(false);
  },[workspaceId]);

  function switchMode(next:"demo"|"live"){
    setMode(next);setResult(null);setError("");
    setText(JSON.stringify(next==="live"?(liveDefaults[id]??{}):(demoDefaults[id]??{}),null,2));
  }

  function replacePayload(next:Record<string,unknown>){
    setText(JSON.stringify(next,null,2));
    setResult(null);setError("");
  }

  function updateField(field:GuidedField,value:string|boolean){
    const next={...(payload??{})};
    next[field.key]=field.type==="number"?(value===""?0:Number(value)):value;
    replacePayload(next);
  }

  function updatePortfolioPosition(index:number,key:"coingecko_id"|"symbol"|"quantity",value:string){
    const positions=[...portfolioPositions];
    positions[index]={...positions[index],[key]:key==="quantity"?(value===""?0:Number(value)):value};
    replacePayload({...payload,manual_positions:positions});
  }

  function addPortfolioPosition(){
    if(portfolioPositions.length>=50)return;
    replacePayload({...payload,manual_positions:[...portfolioPositions,{coingecko_id:"",symbol:"",quantity:0}]});
  }

  function removePortfolioPosition(index:number){
    if(portfolioPositions.length<=1)return;
    replacePayload({...payload,manual_positions:portfolioPositions.filter((_,rowIndex)=>rowIndex!==index)});
  }

  function updateTreasuryAllocation(index:number,key:"coingecko_id"|"symbol"|"weight_pct"|"stablecoin",value:string|boolean){
    const allocations=[...treasuryAllocations];
    allocations[index]={...allocations[index],[key]:key==="weight_pct"?(value===""?0:Number(value)):key==="stablecoin"?Boolean(value):value};
    replacePayload({...payload,allocations});
  }

  function addTreasuryAllocation(){
    if(treasuryAllocations.length>=50)return;
    replacePayload({...payload,allocations:[...treasuryAllocations,{coingecko_id:"",symbol:"",weight_pct:0,stablecoin:false}]});
  }

  function removeTreasuryAllocation(index:number){
    if(treasuryAllocations.length<=1)return;
    replacePayload({...payload,allocations:treasuryAllocations.filter((_,rowIndex)=>rowIndex!==index)});
  }

  async function run(){
    const originWorkspace=workspaceId;
    try{
      setRunning(true);setError("");setResult(null);
      const parsed=JSON.parse(text);
      const path=enginePath[id]??id;
      const r=await api<Record<string,unknown>>(`/api/v1/analysis/${path}`,{method:"POST",body:JSON.stringify({demo:mode==="demo",input:parsed,workspace_id:originWorkspace})});
      if(workspaceRef.current===originWorkspace)setResult(r);
    }catch(e){
      if(workspaceRef.current===originWorkspace)setError(e instanceof Error?e.message:"Analysis failed");
    }finally{
      if(workspaceRef.current===originWorkspace)setRunning(false);
    }
  }

  return <>
    <div className="engineHeader"><div><div className="workspaceKicker">{meta.domain}</div><div className="engineTitleRow"><span>{id}</span><h1>{meta.name}</h1></div><p>{meta.description}</p></div><span className="badge"><span className="statusDot"/>{workspace.name}</span></div>
    <section className="modePanel"><div><span className="workspaceKicker">Execution mode</span><h2>Choose the evidence boundary</h2></div><div className="modeSwitch" role="group" aria-label="Execution mode"><button className={mode==="demo"?"active":""} onClick={()=>switchMode("demo")} aria-pressed={mode==="demo"}><span>01</span><b>Demonstration</b><small>Synthetic, clearly labelled</small></button><button className={mode==="live"?"active":""} disabled={!liveEnabled} onClick={()=>switchMode("live")} aria-pressed={mode==="live"}><span>02</span><b>Live provider analysis</b><small>Verified evidence only</small></button></div><div className={`modeNotice ${mode==="demo"?"demo":"live"}`}><span className="statusDot"/>{mode==="demo"?"Demonstration data only — never represented as institutional live evidence.":"Missing, stale or conflicting provider evidence remains explicit and may produce UNKNOWN."}</div></section>
    <section className="panel inputPanel"><div className="panelHeading"><div><span className="workspaceKicker">Analysis input</span><h2>Configure scenario</h2></div><span className="stepLabel">STEP 2 OF 2</span></div>
      {fields.length>0?<div className="guidedGrid">{fields.map(field=>field.type==="boolean"?<label className="toggleField" key={field.key}><div><b>{field.label}</b><span>{field.hint}</span></div><input type="checkbox" checked={Boolean(payload?.[field.key])} onChange={e=>updateField(field,e.target.checked)}/><span className="toggleTrack"/></label>:<label className="guidedField" key={field.key}><span>{field.label}</span><small>{field.hint}</small>{field.type==="select"?<select value={String(payload?.[field.key]??"")} onChange={e=>updateField(field,e.target.value)}>{field.options?.map(option=><option key={option} value={option}>{option}</option>)}</select>:<input type={field.type} min={field.min} max={field.max} step={field.step} value={String(payload?.[field.key]??"")} onChange={e=>updateField(field,e.target.value)}/>}</label>)}</div>:null}
      {id==="F1"&&mode==="live"?<div className="advancedOnly" data-testid="portfolio-position-builder"><div className="panelHeading"><div><b>Portfolio positions</b><p>Build the canonical <code>manual_positions</code> collection without editing raw JSON. Asset IDs use CoinGecko identifiers; quantity is held as a numeric unit amount.</p></div><span className="stepLabel">{portfolioPositions.length}/50</span></div><div className="tableWrap"><table className="table"><thead><tr><th>#</th><th>CoinGecko asset ID</th><th>Symbol</th><th>Quantity</th><th>Action</th></tr></thead><tbody>{portfolioPositions.map((position,index)=><tr key={index} data-testid="portfolio-position-row"><td>{index+1}</td><td><input aria-label={`Position ${index+1} CoinGecko asset ID`} value={String(position.coingecko_id??"")} onChange={event=>updatePortfolioPosition(index,"coingecko_id",event.target.value)}/></td><td><input aria-label={`Position ${index+1} symbol`} value={String(position.symbol??"")} onChange={event=>updatePortfolioPosition(index,"symbol",event.target.value)}/></td><td><input aria-label={`Position ${index+1} quantity`} type="number" min="0" step="any" value={String(position.quantity??0)} onChange={event=>updatePortfolioPosition(index,"quantity",event.target.value)}/></td><td><button className="ghost" disabled={portfolioPositions.length<=1} onClick={()=>removePortfolioPosition(index)} aria-label={`Remove position ${index+1}`}>Remove</button></td></tr>)}</tbody></table></div><div className="actions"><button className="button" onClick={addPortfolioPosition} disabled={portfolioPositions.length>=50}>Add position</button><span className="muted">Advanced JSON remains available below for integration-specific fields.</span></div></div>:null}
      {id==="F5"&&mode==="live"?<div className="advancedOnly" data-testid="treasury-allocation-builder"><div className="panelHeading"><div><b>Treasury allocation ledger</b><p>Build the canonical <code>allocations</code> collection directly. Rivexis preserves the exact weights entered and does not silently normalize them.</p></div><span className="stepLabel">WEIGHT {treasuryWeightTotal.toFixed(2)}%</span></div><div className="tableWrap"><table className="table"><thead><tr><th>#</th><th>CoinGecko asset ID</th><th>Symbol</th><th>Weight %</th><th>Stablecoin</th><th>Action</th></tr></thead><tbody>{treasuryAllocations.map((allocation,index)=><tr key={index} data-testid="treasury-allocation-row"><td>{index+1}</td><td><input aria-label={`Allocation ${index+1} CoinGecko asset ID`} value={String(allocation.coingecko_id??"")} onChange={event=>updateTreasuryAllocation(index,"coingecko_id",event.target.value)}/></td><td><input aria-label={`Allocation ${index+1} symbol`} value={String(allocation.symbol??"")} onChange={event=>updateTreasuryAllocation(index,"symbol",event.target.value)}/></td><td><input aria-label={`Allocation ${index+1} weight`} type="number" min="0" max="100" step="0.1" value={String(allocation.weight_pct??0)} onChange={event=>updateTreasuryAllocation(index,"weight_pct",event.target.value)}/></td><td><input aria-label={`Allocation ${index+1} stablecoin`} type="checkbox" checked={allocation.stablecoin===true} onChange={event=>updateTreasuryAllocation(index,"stablecoin",event.target.checked)}/></td><td><button className="ghost" disabled={treasuryAllocations.length<=1} onClick={()=>removeTreasuryAllocation(index)} aria-label={`Remove allocation ${index+1}`}>Remove</button></td></tr>)}</tbody></table></div><div className="actions"><button className="button" onClick={addTreasuryAllocation} disabled={treasuryAllocations.length>=50}>Add allocation</button><span className="muted">Weight total is an explicit review cue; the submitted payload retains every entered value.</span></div></div>:null}
      {fields.length===0&&!(id==="F1"&&mode==="live")&&!(id==="F5"&&mode==="live")?<div className="advancedOnly"><b>Structured input</b><p>This engine accepts a collection-based payload. Review or edit the normalized payload below.</p></div>:null}
      <details className="advancedPayload"><summary>Advanced JSON payload <span>For integration and complex inputs</span></summary><label className="field">JSON scenario / provider input<textarea value={text} onChange={e=>{setText(e.target.value);setResult(null);setError("")}} aria-label="Engine input JSON"/></label></details>
      {!payload&&<p className="error" role="alert">The advanced payload is not valid JSON. Correct it before running this engine.</p>}
      <div className="runBar"><div><span>{mode==="demo"?"SYNTHETIC SCENARIO":"LIVE EVIDENCE REQUEST"}</span><small>{id} · {meta.name}</small></div><button className="button runButton" onClick={run} disabled={running||!payload}>{running?<><span className="spinner"/>Running analysis…</>:<>Run {id} analysis <span aria-hidden="true">↗</span></>}</button></div>{error&&<p className="error" role="alert">{error}</p>}
    </section>
    {result&&<section className="panel resultPanel" data-testid="engine-result"><div className="panelHeading"><div><span className="workspaceKicker">Decision record</span><h2>Normalized engine output</h2></div><span className="stepLabel">RECORDED</span></div><ResultSummary result={result}/></section>}
  </>;
}
