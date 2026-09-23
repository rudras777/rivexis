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
    <div className="workspaceHeader"><div><h1>{id} Engine</h1><p>{mode==="demo"?"Run a clearly labelled synthetic demonstration.":"Run against configured provider evidence. Rivexis will return provider-unavailable/partial states rather than inventing data."}</p></div><span className="badge">{workspace.name} · {mode==="demo"?"DEMONSTRATION":"LIVE INPUT"}</span></div>
    <section className="panel"><h2>Execution mode</h2><div style={{display:"flex",gap:8,flexWrap:"wrap"}}><button className="button" onClick={()=>switchMode("demo")} aria-pressed={mode==="demo"}>Demonstration</button><button className="button" disabled={!liveEnabled} onClick={()=>switchMode("live")} aria-pressed={mode==="live"}>Live provider analysis {liveEnabled?"":"(coming next)"}</button></div>{mode==="demo"&&<div className="demoBanner" style={{marginTop:12}}>DEMO DATA / DEMONSTRATION RESULT — not live institutional analysis.</div>}{mode==="live"&&<p className="muted">B1: Tenderly/RPC simulation. B2: direct chain state + deterministic approval rules + optional Etherscan verification. B3: live RPC threat snapshots with prior-state change detection and optional Chainlink feed monitoring; continuous threat streaming still requires a commercial threat provider. B4: direct wallet state + optional Etherscan indexed history with UNKNOWN ADDRESS preserved. B5: LI.FI quote normalization. F1: CoinGecko valuation with optional native-wallet balances. F2: DefiLlama protocol screening. F3: direct Chainlink-compatible feed state with optional CoinGecko cross-check. F4: attributed DefiLlama yield-pool evidence. F5: CoinGecko-referenced allocation and stress screening. Missing institutional evidence remains explicit.</p>}</section>
    <section className="panel"><h2>Input</h2><label className="field">JSON scenario / provider input<textarea value={text} onChange={e=>setText(e.target.value)} aria-label="Engine input JSON"/></label><button className="button" onClick={run} disabled={running} style={{marginTop:12}}>{running?"Running…":`Run ${id}`}</button>{error&&<p className="error" role="alert">{error}</p>}</section>
    {result&&<section className="panel" data-testid="engine-result"><h2>Normalized engine output</h2><div className={result.demo?"demoBanner":""}>{result.demo?"DEMONSTRATION RESULT":"Provider-grounded result / explicit degraded state"}</div><pre className="result">{JSON.stringify(result,null,2)}</pre></section>}
  </>;
}
