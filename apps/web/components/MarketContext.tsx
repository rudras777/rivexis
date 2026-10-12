"use client";
import {createContext,useContext,useEffect,useRef,useState} from 'react';
import {usePathname} from 'next/navigation';
import {useAccountPreferences} from './AccountPreferences';
import {readMarket,mergeMarketSamples,type MarketSnapshot,type FeeSample,type OracleQuote} from '@/lib/market-feed.mjs';
import {ObservationChart} from './ObservationChart';
type State={data:MarketSnapshot|null;fees:FeeSample[];quotes:{ETH:OracleQuote[];BTC:OracleQuote[]};error:string;notice:string;busy:boolean;visible:boolean;refresh:()=>void};
const Context=createContext<State|null>(null);
export function MarketContextProvider({children}:{children:React.ReactNode}){
 const path=usePathname(),{account}=useAccountPreferences(),[data,setData]=useState<MarketSnapshot|null>(null),[fees,setFees]=useState<FeeSample[]>([]),[quotes,setQuotes]=useState<{ETH:OracleQuote[];BTC:OracleQuote[]}>({ETH:[],BTC:[]}),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[visible,setVisible]=useState(true),[request,setRequest]=useState(0);
 const last=useRef(0),dataRef=useRef(data),consumedRequest=useRef(0);dataRef.current=data;
 const enabled=!!account?.profile.emailVerified&&['/workspace/overview','/workspace/transactions','/workspace/networks'].includes(path);
 useEffect(()=>{const update=()=>setVisible(!document.hidden);update();document.addEventListener('visibilitychange',update);return()=>document.removeEventListener('visibilitychange',update)},[]);
 useEffect(()=>{if(!account?.profile.emailVerified){setData(null);setFees([]);setQuotes({ETH:[],BTC:[]});last.current=0}},[account?.profile.emailVerified]);
 useEffect(()=>{
  if(!enabled||!visible)return;let cancelled=false,timer:ReturnType<typeof setTimeout>,failures=0,inflight=false;const controller=new AbortController();
  async function check(){if(cancelled||inflight)return;inflight=true;setBusy(true);try{const next=await readMarket({signal:controller.signal,history:!dataRef.current});if(cancelled)return;
   setFees(old=>{try{return mergeMarketSamples(old,next.fees,96)}catch{return next.fees}});
   setQuotes(old=>{const merged={...old};for(const symbol of ['ETH','BTC'] as const){const incoming=[...next.history[symbol],...(next.quotes[symbol]?[next.quotes[symbol]!]:[])];const byTime=new Map([...old[symbol],...incoming].map(q=>[q.updatedAt,q]));merged[symbol]=[...byTime.values()].sort((a,b)=>a.updatedAt-b.updatedAt).slice(-96)}return merged});
   dataRef.current=next;setData(next);last.current=Date.now();setError('');setNotice('');failures=0;
  }catch(e){if(!cancelled){setError(e instanceof Error?e.message:'Provider observations unavailable');failures++}}finally{inflight=false;if(!cancelled){setBusy(false);timer=setTimeout(()=>void check(),Math.min(300000,60000*2**Math.min(failures,3)))}}}
  const manual=request>consumedRequest.current;consumedRequest.current=request;if(Date.now()-last.current>=45000||manual)void check();else timer=setTimeout(()=>void check(),Math.max(1000,60000-(Date.now()-last.current)));
  return()=>{cancelled=true;controller.abort();clearTimeout(timer);setBusy(false)};
 },[enabled,visible,request]);
 return <Context.Provider value={{data,fees,quotes,error,notice,busy,visible,refresh:()=>{if(Date.now()-last.current<15000){setNotice('Wait 15 seconds between manual network refreshes.');return}setRequest(n=>n+1)}}}>{children}</Context.Provider>;
}
export function LiveMarketContext({networkOnly=false}:{networkOnly?:boolean}){
 const state=useContext(Context),[clock,setClock]=useState(Date.now());useEffect(()=>{const timer=setInterval(()=>setClock(Date.now()),5000);return()=>clearInterval(timer)},[]);
 if(!state)return null;const {data,error,notice,busy,quotes,fees,visible}=state,blockAge=data?Math.max(0,Math.floor(clock/1000-data.block.timestamp)):null;
 return <section className="instrumentPanel" aria-label="Live on-chain market context"><div className="sectionHeading"><h2>{networkOnly?'Ethereum network observations':'Market and network observations'}</h2><button type="button" className="textButton" disabled={busy||!visible} onClick={state.refresh}>{busy?'Reading public observations…':'Refresh market context'}</button></div><p role="status">{!visible?'Paused while this tab is hidden':busy&&!data?'Connecting':error?'Provider unavailable; retained observations may be stale':data&&blockAge!>90?'Stale block observation':data?'Fresh block observation':'No observation yet'}</p>{error&&<p className="warning">{error}</p>}{notice&&<p role="status">{notice}</p>}
 <p className="muted">Ethereum mainnet · PublicNode JSON-RPC · visible-tab polling every minute, with bounded retry backoff. Oracle quotes are Chainlink observations, separate from each lending protocol’s authoritative risk oracle. No signing or trading.</p>
 {data&&<><p className="previewProvenance">Block {data.block.number} · observed {new Date(data.observedAt*1000).toISOString()} · block age {blockAge}s</p><details><summary>Market observation provenance</summary><p className="mono">{data.block.hash}</p><p>Source: {data.source}. History uses only returned observations; archive and earlier-round gaps remain explicit. No fixed 24-hour coverage is promised.</p>{data.history.errors.map((e,i)=><p className="muted" key={i}>{e}</p>)}</details>
 {!networkOnly&&<div className="twoColumns">{(['ETH','BTC'] as const).map(symbol=>{const quote=data.quotes[symbol],age=quote?Math.max(0,Math.floor(clock/1000-quote.updatedAt)):null;const series=quotes[symbol];const day=[...series].reverse().find(q=>q.updatedAt<=clock/1000-86400&&clock/1000-86400-q.updatedAt<=180);return <div key={symbol}><h3>{symbol} / USD oracle context</h3><p>{quote?`$${quote.priceUsd.toLocaleString('en-US',{maximumFractionDigits:4})}`:'Unavailable'} · {quote?(error?'Latest quote not reverified':age!>3600?'Stale oracle round':'Fresh oracle round'):'No validated quote'}</p>{quote&&<p className="muted">Feed update {new Date(quote.updatedAt*1000).toISOString()} · age {age}s · round {quote.roundId}</p>}<p className="muted">24h change: {quote&&day?`${((quote.priceUsd/day.priceUsd-1)*100).toFixed(2)}% (sparse oracle observations)`:'Unavailable: no validated observation at or before the 24h boundary'}</p>{data.quoteErrors[symbol]&&<p className="warning">{data.quoteErrors[symbol]}</p>}<ObservationChart title={`${symbol} / USD · observed oracle history`} unit="USD" points={series.map(q=>({time:q.updatedAt,value:q.priceUsd}))} maxGap={7200} empty="No validated historical rounds returned. Missing observations are not filled."/></div>})}</div>}
 {data.feeError&&<p className="warning">Fee history unavailable: {data.feeError}</p>}<ObservationChart title="Ethereum observed base fee history" unit="gwei" points={fees.map(f=>({time:f.timestamp,value:Number(BigInt(f.baseFeeWei))/1e9}))} maxGap={180}/><p className="muted">Base fee is the observed EIP-1559 component, not a total transaction fee or priority-fee promise. GasGuard still obtains independent call-specific estimates. Historical points use actual block timestamps.</p></>}
 {!data&&!busy&&<p>No fabricated market series is shown. Retry when the provider is available.</p>}</section>;
}
