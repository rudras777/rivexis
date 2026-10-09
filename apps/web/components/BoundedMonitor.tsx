"use client";
import {useEffect,useRef,useState} from "react";
import {useDeFi} from "./DeFiContext";
import {format,type Snapshot} from "../../../supabase/functions/rivexis-api/defi-model.mjs";
export function BoundedMonitor(){
  const c=useDeFi(),[active,setActive]=useState(false),[checks,setChecks]=useState(0),[status,setStatus]=useState(""),latest=useRef(c);
  latest.current=c;
  useEffect(()=>{
    if(!active)return;
    const wallet=c.snapshot?.wallet,coverage=c.snapshot?.coverage??"aave";if(!wallet||c.snapshot?.sample){setActive(false);return}
    let used=0,busy=false,cancelled=false;const controller=new AbortController();
    const stop=(message:string)=>{setStatus(message);setActive(false)};
    async function check(){
      if(cancelled||busy)return;
      if(document.visibilityState!=="visible"){stop("Checks stopped because the tab is hidden.");return}
      if(latest.current.snapshot?.wallet!==wallet||latest.current.snapshot?.coverage!==coverage&&!(coverage==="aave"&&latest.current.snapshot?.coverage===undefined)){stop("Checks stopped because the inspected wallet changed.");return}
      busy=true;
      try{
        const r=await fetch('/api/v1/defi/snapshot',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({wallet,coverage}),signal:controller.signal});
        const body=await r.json();if(!r.ok)throw new Error(body.detail||'Evidence unavailable');
        if(cancelled)return;
        latest.current.setSnapshot(body as Snapshot);latest.current.setResult(null);used++;setChecks(used);
        setStatus(`Check ${used} of 5 complete. Latest block: ${body.blockNumber}.`);
        if(used>=5)stop("Five checks complete. Monitoring stopped; restart explicitly if needed.");
      }catch(e){if(!cancelled)stop(e instanceof Error?e.message:'Evidence unavailable; monitoring stopped')}finally{busy=false}
    }
    void check();const timer=setInterval(()=>void check(),120000);
    return()=>{cancelled=true;controller.abort();clearInterval(timer)};
  },[active]);
  const previous=c.previousSnapshot,current=c.snapshot;
  return <section className="instrumentPanel"><div className="eyebrow">BOUNDED / IN-BROWSER MONITORING</div><h2>Check for changes, with limits.</h2><p>Run up to five on-chain checks, two minutes apart, while this view remains open and visible. Global beta quotas apply. Checks stop on provider failure or quota exhaustion.</p><button className="ghost" disabled={!current||!!current.sample} type="button" onClick={()=>{setChecks(0);setStatus("");setActive(!active)}}>{active?"Stop checks":"Start five bounded checks"}</button><p className="muted" role="status">{status||"No background monitoring is active."}</p>{previous&&current&&<div className="metricRibbon"><div><span>Previous block</span><strong>{previous.blockNumber}</strong></div><div><span>Current block</span><strong>{current.blockNumber}</strong></div><div><span>Previous observed health</span><strong>{previous.observedHealthFactorRaw?format(previous.observedHealthFactorRaw,18,3):"No debt"}</strong></div><div><span>Current observed health</span><strong>{current.observedHealthFactorRaw?format(current.observedHealthFactorRaw,18,3):"No debt"}</strong></div></div>}<p className="muted">This is a bounded browser check, not continuous surveillance or an email alert service. It cannot guarantee a warning before liquidation.</p></section>;
}
