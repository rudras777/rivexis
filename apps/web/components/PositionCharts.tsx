"use client";
import {ObservationChart} from './ObservationChart';
import {scenario,format,type Snapshot} from '../../../supabase/functions/rivexis-api/defi-unified-model.mjs';
export function PositionCharts({snapshot,history,shocks,now}:{snapshot:Snapshot;history:Snapshot[];shocks:Record<string,number>;now:number}){
 const sample=!!snapshot.sample,restored=!!snapshot.restoredReport;
 if(!sample&&!restored&&now/1000-snapshot.blockTimestamp>180)return <p className="warning">Risk charts withheld: refresh the stale position evidence.</p>;
 const rawMoney=(v:unknown)=>typeof v==='string'&&/^\d+$/.test(v)?Number(format(v,8,4)):NaN;
 return <section aria-label="Position charts"><div className="sectionHeading"><h2>Position observations and sensitivity</h2><span className="modeLabel">{sample?'Hypothetical sample':restored?'Historical receipt':`Observed block ${snapshot.blockNumber}`}</span></div>
 {snapshot.positions.map((position,index)=>{const asset=position.reserves.find(r=>r.collateralEnabled&&BigInt(r.collateralRaw)>0n);if(!asset)return <p key={position.id} className="muted">{position.protocol}: no eligible collateral reference for a sensitivity curve.</p>;const points=[];for(let shock=-9500;shock<=10000;shock+=500){try{const result=scenario(snapshot,{...shocks,[asset.asset.toLowerCase()]:shock},[],sample||restored?snapshot.blockTimestamp*1000:now)[index];if(result?.healthFactorRaw!==null&&result?.healthFactorRaw!==undefined)points.push({time:shock/100,value:Number(format(result.healthFactorRaw,18,6)),label:`${asset.symbol} price shock ${shock/100}%`,rawHealth:result.healthFactorRaw})}catch{}}
 return <ObservationChart key={position.id} title={`${position.protocol} · health sensitivity to ${asset.symbol}`} unit="HF" pointKind="modeled" reference={1} points={points} empty="No finite modeled health factor for this position (for example, no debt or unsupported evidence)."/>})}
 <p className="muted">Sensitivity curves are explicit hypothetical price shocks, not price forecasts or historical market data. Other user shocks, debt and protocol parameters are held fixed. Separate positions are not netted.</p>
 {!sample&&!restored&&<><ObservationChart title="Observed collateral value history" unit="USD" points={history.map(s=>({time:s.blockTimestamp,value:rawMoney(s.observedCollateralRaw)}))} empty="History starts with verified reads in this browser session. Refresh or start bounded monitoring to collect observations." maxGap={300}/><p className="muted">Up to 48 real snapshot observations in this session; gaps are not interpolated. Changing wallet, coverage or account clears the series. Saved receipts retain their own original block evidence.</p></>}
 </section>;
}
