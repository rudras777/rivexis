"use client";
import {createContext,useContext,useEffect,useRef,useState} from 'react';
import {usePathname} from 'next/navigation';
import {useAccountPreferences} from './AccountPreferences';
import {readMarket,mergeMarketWindow,type MarketSnapshot,type FeeSample,type OracleQuote} from '@/lib/market-feed.mjs';
import {ObservationChart} from './ObservationChart';
import {ExchangeChart} from './ExchangeChart';
type State={data:MarketSnapshot|null;fees:FeeSample[];quotes:{ETH:OracleQuote[];BTC:OracleQuote[]};error:string;notice:string;busy:boolean;visible:boolean;refresh:()=>void};
const Context=createContext<State|null>(null);
export function MarketContextProvider({children}:{children:React.ReactNode}){
 const {account}=useAccountPreferences();
 return <MarketSession owner={account?.profile.emailVerified?account.profile.email:'guest'}>{children}</MarketSession>;
}
function MarketSession({children,owner}:{children:React.ReactNode;owner:string}){
 const path=usePathname(),{account}=useAccountPreferences(),[data,setData]=useState<MarketSnapshot|null>(null),[fees,setFees]=useState<FeeSample[]>([]),[quotes,setQuotes]=useState<{ETH:OracleQuote[];BTC:OracleQuote[]}>({ETH:[],BTC:[]}),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[visible,setVisible]=useState(true),[request,setRequest]=useState(0);
 const last=useRef(0),lastAttempt=useRef(0),dataRef=useRef(data),windowRef=useRef({fees,quotes}),consumedRequest=useRef(0),historyNeeded=useRef(true),nextHistoryAttempt=useRef(0),failuresRef=useRef(0),nextPollAt=useRef(0);dataRef.current=data;
 const enabled=!!account?.profile.emailVerified&&['/workspace/overview','/workspace/transactions','/workspace/networks'].includes(path);
 useEffect(()=>{const update=()=>setVisible(!document.hidden);update();document.addEventListener('visibilitychange',update);return()=>document.removeEventListener('visibilitychange',update)},[]);
 // Reset only public market state. A keyed provider would remount the entire
 // financial workspace when profile hydration completes and discard user input.
 useEffect(()=>{const empty={fees:[],quotes:{ETH:[],BTC:[]}};dataRef.current=null;windowRef.current=empty;setData(null);setFees([]);setQuotes(empty.quotes);setError('');setNotice('');last.current=0;lastAttempt.current=0;historyNeeded.current=true;nextHistoryAttempt.current=0;failuresRef.current=0;nextPollAt.current=0},[owner]);
 useEffect(()=>{
  if(!enabled||!visible)return;let cancelled=false,timer:ReturnType<typeof setTimeout>,inflight=false;const controller=new AbortController();
  async function check(){if(cancelled||inflight)return;inflight=true;lastAttempt.current=Date.now();setBusy(true);try{
   // Retry missing history on the existing visible-tab poll, at most every five
   // minutes; a healthy quote poll must not permanently latch an empty history.
   const history=!dataRef.current||(historyNeeded.current&&Date.now()>=nextHistoryAttempt.current);
   if(history)nextHistoryAttempt.current=Date.now()+300000;
   const next=await readMarket({signal:controller.signal,history});if(cancelled)return;
   if(history)historyNeeded.current=(['ETH','BTC'] as const).some(symbol=>new Set([...next.history[symbol],...(next.quotes[symbol]?[next.quotes[symbol]!]:[])].map(q=>q.updatedAt)).size<2);
   const merged=mergeMarketWindow(dataRef.current,next,windowRef.current.fees,windowRef.current.quotes);windowRef.current=merged;setFees(merged.fees);setQuotes(merged.quotes);
   dataRef.current=next;setData(next);last.current=Date.now();setError('');setNotice(merged.reset?'Chain history changed; prior price and fee observations were discarded.':'');failuresRef.current=0;
  }catch(e){if(!cancelled){setError(e instanceof Error?e.message:'Provider observations unavailable');failuresRef.current++}}finally{inflight=false;if(!cancelled){setBusy(false);const delay=Math.min(300000,60000*2**Math.min(failuresRef.current,3));nextPollAt.current=Date.now()+delay;timer=setTimeout(()=>void check(),delay)}}}
  const manual=request>consumedRequest.current;consumedRequest.current=request;if(Date.now()>=nextPollAt.current||manual)void check();else timer=setTimeout(()=>void check(),Math.max(1000,nextPollAt.current-Date.now()));
  return()=>{cancelled=true;controller.abort();clearTimeout(timer);setBusy(false)};
 },[enabled,visible,request,owner]);
 return <Context.Provider value={{data,fees,quotes,error,notice,busy,visible,refresh:()=>{if(Date.now()-lastAttempt.current<15000){setNotice('Wait 15 seconds between manual network refreshes.');return}setRequest(n=>n+1)}}}>{children}</Context.Provider>;
}
export function LiveMarketContext({networkOnly=false}:{networkOnly?:boolean}){
 const {preferences}=useAccountPreferences();
 const state=useContext(Context),[clock,setClock]=useState(Date.now());useEffect(()=>{const timer=setInterval(()=>setClock(Date.now()),5000);return()=>clearInterval(timer)},[]);
 if(!state)return null;const {data,error,notice,busy,quotes,fees,visible}=state,blockAge=data?Math.max(0,Math.floor(clock/1000-data.block.timestamp)):null;
 const timestamp=(value:number)=>new Date(value*1000).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC';
 return <section className="instrumentPanel marketContext" aria-label="Live on-chain market context">
 <header className="sectionHeading"><div><span className="marketEyebrow">Ethereum mainnet</span><h2>{networkOnly?'Network conditions':'Market context'}</h2><p className="marketIntro">{networkOnly?'Observed fees and block activity.':'Reference oracle observations, with optional exchange context.'}</p></div><button type="button" className="ghost marketRefresh" disabled={busy||!visible} onClick={state.refresh}>{busy?'Reading public observations…':'Refresh market context'}</button></header>
 {!networkOnly&&<ExchangeChart/>}
 <div className="marketStatusLine"><span className="marketFreshness" role="status">{!visible?'Paused while this tab is hidden':busy&&!data?'Connecting':error?'Provider unavailable; retained observations may be stale':data&&blockAge!>90?'Stale block observation':data?'Fresh block observation':'No observation yet'}</span>{data&&<span>Block {data.block.number} · {blockAge}s old</span>}</div>
 {error&&<p className="warning">{error}</p>}{notice&&<p role="status">{notice}</p>}
 {data&&<>
 {!networkOnly&&<div className="marketQuoteGrid">{(['ETH','BTC'] as const).map(symbol=>{const quote=data.quotes[symbol],age=quote?Math.max(0,Math.floor(clock/1000-quote.updatedAt)):null;const series=quotes[symbol];const day=[...series].reverse().find(q=>q.updatedAt<=clock/1000-86400&&clock/1000-86400-q.updatedAt<=180);return <article className="marketQuote" key={symbol}>
 <div className="marketAssetHeading"><h3>{symbol==='ETH'?'Ethereum':'Bitcoin'}</h3><span>{symbol} / USD</span></div>
 <strong className="marketPrice">{quote?`$${quote.priceUsd.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:4,useGrouping:preferences.numberGrouping})}`:'Unavailable'}</strong>
 <p className="marketQuoteStatus">{quote?(error||(blockAge!==null&&blockAge>90)?'Latest quote not reverified':age!>3600?'Stale oracle round':'Fresh oracle round'):'No validated quote'}{quote&&` · updated ${timestamp(quote.updatedAt)}`}</p>
 <details><summary>{symbol} / USD · oracle observations</summary><ObservationChart title={`${symbol} / USD · observed oracle history`} unit="USD" points={series.map(q=>({time:q.updatedAt,value:q.priceUsd}))} maxGap={7200} empty="No validated historical rounds returned. Missing observations are not filled."/></details>
 <p className="marketChange">24h change: {quote&&day?`${((quote.priceUsd/day.priceUsd-1)*100).toFixed(2)}% (sparse oracle observations)`:'Unavailable — insufficient historical coverage'}</p>{data.quoteErrors[symbol]&&<p className="warning">{data.quoteErrors[symbol]}</p>}</article>})}</div>}
 <div className="marketFee"><ObservationChart title="Ethereum observed base fee history" unit="gwei" points={fees.map(f=>({time:f.timestamp,value:Number(BigInt(f.baseFeeWei))/1e9}))} maxGap={180}/><p className="muted">Base fee is one part of a transaction fee. GasGuard obtains independent call-specific estimates.</p>{data.feeError&&<p className="warning">Fee history unavailable: {data.feeError}</p>}</div>
 <details className="marketEvidence"><summary>Market observation provenance</summary><p>Ethereum mainnet · PublicNode JSON-RPC · visible-tab polling every minute, with bounded retry backoff. Oracle quotes are Chainlink observations, separate from each lending protocol’s authoritative risk oracle. No signing or trading.</p><p>Received {timestamp(data.observedAt)} · block age {blockAge}s</p><p className="mono">{data.block.hash}</p><p>Source: {data.source}. History uses only returned observations; archive and earlier-round gaps remain explicit. No fixed 24-hour coverage is promised. A missing24-hour comparison is unavailable. Historical price points use returned oracle update times, with observation block provenance retained; no missing prices are filled.</p>{(['ETH','BTC'] as const).map(symbol=>data.quotes[symbol]&&<p key={symbol}>{symbol} / USD · Chainlink feed <code>{data.quotes[symbol]!.feed}</code> · raw answer {data.quotes[symbol]!.answerRaw} / 10⁸ · round {data.quotes[symbol]!.roundId} · source updated {timestamp(data.quotes[symbol]!.updatedAt)}</p>)}{data.history.errors.map((e,i)=><p className="muted" key={i}>{e}</p>)}</details></>}
 {!data&&!busy&&<p>Market observations are unavailable. Retry when the provider is available.</p>}</section>;
}
