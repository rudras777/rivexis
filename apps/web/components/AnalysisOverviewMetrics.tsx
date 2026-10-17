"use client";
import {useEffect,useState} from 'react';
import {InfoButton} from './InfoButton';
import {displayedMoney} from '@/lib/financial-display';
import type {Snapshot} from '../../../supabase/functions/rivexis-api/defi-model.mjs';

export function AnalysisOverviewMetrics({snapshot,grouping}:{snapshot:Snapshot|null;grouping:boolean}){
 const [clock,setClock]=useState(()=>Date.now());
 useEffect(()=>{
  if(!snapshot||snapshot.sample||snapshot.restoredReport)return;
  const update=()=>{if(!document.hidden)setClock(Date.now())};
  update();const timer=setInterval(update,10000);
  document.addEventListener('visibilitychange',update);window.addEventListener('focus',update);
  return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',update);window.removeEventListener('focus',update)};
 },[snapshot]);
 const time=snapshot?.blockTimestamp,validTime=typeof time==='number'&&Number.isSafeInteger(time)&&time>0;
 const future=validTime&&time>clock/1000+30;
 const age=validTime?Math.max(0,Math.floor(clock/1000-time)):null;
 const expired=validTime&&clock/1000-time>180;
 const sample=!!snapshot?.sample,historical=!!snapshot?.restoredReport;
 const verified=!!snapshot&&snapshot.status==='READY'&&validTime&&!future;
 const show=sample||historical||verified;
 const hint=!snapshot?'Inspect a wallet to view this metric':sample?'Hypothetical sample · not live':historical?'Historical receipt · refresh before analysis':snapshot.status!=='READY'?'Unvalidated snapshot · inspect again':!validTime?'Snapshot time unavailable · inspect again':future?'Snapshot time is ahead of this device · refresh evidence':expired?'Stale snapshot · refresh in LiquidationGuard':`Observed snapshot · ${age}s old`;
 const money=(value:unknown)=>show&&typeof value==='string'&&/^\d{1,78}$/.test(value)?displayedMoney(value,grouping):'—';
 return <div className="portfolioMetrics" role="region" aria-label="Current analysis overview">
  {['Collateral value','Outstanding debt','Evidence block'].map((name,i)=><article className="overviewMetric" key={name}>
   <span>{name}<InfoButton label={name}>{i===0?'Collateral value in USD at the inspected snapshot. It is not continuously revalued.':i===1?'Lending debt in USD at the inspected snapshot. New interest and price changes require refreshed evidence.':'The Ethereum block used for this snapshot. Sample, historical and stale inputs are not current evidence.'}</InfoButton></span>
   <strong>{i===2?(sample?'Not on-chain':show&&snapshot?`#${snapshot.blockNumber}`:'—'):money(i===0?snapshot?.observedCollateralRaw:snapshot?.observedDebtRaw)}</strong>
   <small>{hint}</small>
  </article>)}
 </div>;
}
