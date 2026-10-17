"use client";
import {useEffect,useRef,useState} from "react";
import {api} from "@/lib/api";
import {useAccountPreferences} from "./AccountPreferences";
import {useDeFi} from "./DeFiContext";
import {format,type Snapshot} from "../../../supabase/functions/rivexis-api/defi-model.mjs";
const identityOf=(snapshot:Snapshot|null)=>snapshot&&!snapshot.sample&&typeof snapshot.wallet==='string'?`${snapshot.wallet.toLowerCase()}:${snapshot.coverage??'aave'}`:null;
export function BoundedMonitor(){
 const {preferences}=useAccountPreferences();
  const c=useDeFi(),[active,setActive]=useState(false),[checks,setChecks]=useState(0),[status,setStatus]=useState(""),latest=useRef(c);
  latest.current=c;
  const identity=identityOf(c.snapshot),sessionIdentity=useRef<string|null>(null),stopSession=useRef<((message:string)=>void)|null>(null);
  useEffect(()=>{
    if(active&&stopSession.current&&identity!==sessionIdentity.current)stopSession.current('Checks stopped because the inspected wallet or coverage changed.');
  },[active,identity]);
  useEffect(()=>{
    if(!active)return;
    const wallet=c.snapshot?.wallet,coverage=c.snapshot?.coverage??"aave",expected=identityOf(c.snapshot);if(!wallet||!expected||c.snapshot?.status!=='READY'){setActive(false);return}
    let used=0,busy=false,cancelled=false;const controller=new AbortController();
    let timer:ReturnType<typeof setInterval>|undefined;
    const stop=(message:string)=>{if(cancelled)return;cancelled=true;controller.abort();clearInterval(timer);setStatus(message);setActive(false)};
    stopSession.current=stop;sessionIdentity.current=expected;
    const matches=()=>identityOf(latest.current.snapshot)===expected;
    const visibility=()=>{if(document.visibilityState!=='visible')stop('Checks stopped because the tab is hidden.')};
    const walletChanged=()=>stop('Checks stopped because wallet access changed.');
    const workspaceChanged=()=>stop('Checks stopped because the active workspace changed.');
    async function check(){
      if(cancelled||busy)return;
      if(document.visibilityState!=="visible"){stop("Checks stopped because the tab is hidden.");return}
      if(!matches()){stop('Checks stopped because the inspected wallet or coverage changed.');return}
      busy=true;
      try{
        const body=await api<Snapshot>('/api/v1/defi/snapshot',{method:'POST',body:JSON.stringify({wallet,coverage}),signal:AbortSignal.any([controller.signal,AbortSignal.timeout(35000)])});
        if(cancelled)return;
        if(!matches()){stop('Checks stopped because the inspected wallet or coverage changed.');return}
        if(document.visibilityState!=='visible'){visibility();return}
        if(identityOf(body)!==expected||body.restoredReport)throw new Error('Returned evidence did not match the monitored wallet and coverage.');
        if(body.status!=='READY')throw new Error('Returned evidence is unsupported; inspect the position again.');
        const age=Date.now()/1000-body.blockTimestamp;
        if(!Number.isFinite(body.blockTimestamp)||body.blockTimestamp<=0||age>180||age< -30)throw new Error('Returned evidence is stale or has an invalid observation time.');
        if(!/^\d+$/.test(body.blockNumber))throw new Error('Returned evidence has an invalid block identity.');
        const current=latest.current.snapshot;
        if(current&&/^\d+$/.test(current.blockNumber)&&BigInt(body.blockNumber)<BigInt(current.blockNumber))throw new Error('A newer inspection is already available; older monitoring evidence was discarded.');
        latest.current.setSnapshot(body);latest.current.setResult(null);used++;setChecks(used);
        setStatus(`Check ${used} of 5 complete. Latest block: ${body.blockNumber}.`);
        if(used>=5)stop("Five checks complete. Monitoring stopped; restart explicitly if needed.");
      }catch(e){if(!cancelled)stop(`${e instanceof Error?e.message:'Evidence unavailable.'} Monitoring stopped.`)}finally{busy=false}
    }
    document.addEventListener('visibilitychange',visibility);window.addEventListener('rivexis-wallet-context-change',walletChanged);window.addEventListener('rivexis-workspace-change',workspaceChanged);
    timer=setInterval(()=>void check(),120000);void check();
    return()=>{cancelled=true;controller.abort();clearInterval(timer);document.removeEventListener('visibilitychange',visibility);window.removeEventListener('rivexis-wallet-context-change',walletChanged);window.removeEventListener('rivexis-workspace-change',workspaceChanged);if(stopSession.current===stop)stopSession.current=null};
  },[active]);
  const previous=c.previousSnapshot,current=c.snapshot;
  function toggle(){setChecks(0);if(active){stopSession.current?.('Checks stopped. Restart explicitly when ready.');setActive(false)}else{setStatus('');setActive(true)}}
  return <section className="instrumentPanel">
    <div className="eyebrow">BOUNDED / IN-BROWSER MONITORING</div>
    <h2>Check for changes, with limits.</h2>
    <p>Run up to five on-chain checks, two minutes apart, while this view remains open and visible. Global beta quotas apply. Checks stop on provider failure or quota exhaustion.</p>
    <button className="ghost" disabled={!active&&(!current||!!current.sample||current.status!=='READY')} type="button" onClick={toggle}>{active?"Stop checks":"Start five bounded checks"}</button>
    <p className="muted" role="status">{status||"No background monitoring is active."}</p>
    {previous&&current&&<div className="metricRibbon">
      <div><span>Previous block</span><strong>{previous.blockNumber}</strong></div>
      <div><span>Current block</span><strong>{current.blockNumber}</strong></div>
      <div><span>Previous observed health</span><strong>{previous.observedHealthFactorRaw?format(previous.observedHealthFactorRaw,18,preferences.healthPrecision):"No debt"}</strong></div>
      <div><span>Current observed health</span><strong>{current.observedHealthFactorRaw?format(current.observedHealthFactorRaw,18,preferences.healthPrecision):"No debt"}</strong></div>
    </div>}
    <p className="muted">This is a bounded browser check, not continuous surveillance or an email alert service. It cannot guarantee a warning before liquidation.</p>
  </section>;
}
