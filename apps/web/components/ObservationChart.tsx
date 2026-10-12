"use client";
import {useId,useState} from 'react';
export type ChartPoint={time:number;value:number;label?:string};
export function ObservationChart({title,unit,points,empty='No validated observations available.',maxGap=Infinity,reference,pointKind='observed'}:{title:string;unit:string;points:ChartPoint[];empty?:string;maxGap?:number;reference?:number;pointKind?:'observed'|'modeled'}){
 const id=useId(),[active,setActive]=useState<number|null>(null),valid=points.filter(p=>Number.isFinite(p.time)&&Number.isFinite(p.value)&&p.value>=0).sort((a,b)=>a.time-b.time);
 if(!valid.length)return <figure className="frontierChart observationChart"><figcaption><strong>{title}</strong></figcaption><p role="status">{empty}</p></figure>;
 const low=Math.min(...valid.map(p=>p.value)),high=Math.max(...valid.map(p=>p.value)),pad=Math.max((high-low)*.12,high*.001,.000001),min=Math.max(0,low-pad),max=high+pad,first=valid[0].time,last=valid[valid.length-1].time;
 const x=(p:ChartPoint)=>76+(p.time-first)/Math.max(1,last-first)*570,y=(p:ChartPoint)=>205-(p.value-min)/(max-min)*165;
 const groups:ChartPoint[][]=[];for(const p of valid){const previous=groups[groups.length-1];if(!previous||p.time-previous[previous.length-1].time>maxGap)groups.push([p]);else previous.push(p)}
 const number=(v:number)=>v.toLocaleString('en-US',{maximumFractionDigits:unit==='HF'?3:4});
 const time=(p:ChartPoint)=>p.label??new Date(p.time*1000).toISOString().replace('T',' ').slice(0,19)+' UTC';
 const shortTime=(p:ChartPoint)=>p.label?.replace(' price shock ',' ')??new Date(p.time*1000).toLocaleString('en-GB',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC';
 const selected=valid[Math.min(active??valid.length-1,valid.length-1)];
 const axis=(v:number)=>unit==='USD'?'$'+v.toLocaleString('en-US',{maximumFractionDigits:0}):number(v);
 return <figure className="frontierChart observationChart"><figcaption id={id}><strong>{title}</strong><span>{unit} · {valid.length} {pointKind} points. Hover points or open the data table for {pointKind} values.</span></figcaption>
 <div className="chartReadout" aria-live="polite"><strong>{unit==='USD'?'$':''}{number(selected.value)}{unit!=='USD'&&` ${unit}`}</strong><span>{time(selected)}</span></div>
 <svg viewBox="0 0 720 260" role="img" aria-labelledby={id} aria-describedby={`${id}-help`} tabIndex={0} onKeyDown={e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();setActive(i=>Math.max(0,Math.min(valid.length-1,(i??valid.length-1)+(e.key==='ArrowLeft'?-1:1))))}}}>
 {[0,.5,1].map(t=>{const value=min+(max-min)*t,vertical=205-t*165;return <g key={t}><path d={`M76 ${vertical}H646`} fill="none" stroke="var(--border)" strokeDasharray={t===0?undefined:'3 6'}/><text className="chartAxisLabel" x="66" y={vertical+4} textAnchor="end" fill="var(--secondary)" fontSize="13">{axis(value)}</text></g>})}
 {reference!==undefined&&reference>=min&&reference<=max&&<><path d={`M76 ${205-(reference-min)/(max-min)*165}H646`} stroke="var(--bronze)" strokeDasharray="5 5"/><text x="82" y={200-(reference-min)/(max-min)*165} fill="var(--bronze)" fontSize="12">{unit==='HF'&&reference===1?'Liquidation threshold · HF 1':`Reference ${reference} ${unit}`}</text></>}
 {groups.map((g,i)=><polyline key={i} points={g.map(p=>`${x(p)},${y(p)}`).join(' ')} fill="none" stroke="var(--soft)" strokeWidth="2.2"/>)}
 {valid.map((p,i)=><circle key={`${p.time}:${i}`} cx={x(p)} cy={y(p)} r={p===selected?5:3.5} fill={p===selected?'var(--text)':'var(--soft)'} stroke="var(--surface)" strokeWidth="1.5" onMouseEnter={()=>setActive(i)} onPointerDown={()=>setActive(i)}><title>{time(p)} · {number(p.value)} {unit}</title></circle>)}
 <text className="chartAxisLabel" x="76" y="239" fill="var(--secondary)" fontSize="13">{shortTime(valid[0])}</text><text className="chartAxisLabel" x="646" y="255" textAnchor="end" fill="var(--secondary)" fontSize="13">{shortTime(valid[valid.length-1])}</text></svg>
 <p id={`${id}-help`} className="chartHelp">{pointKind==='modeled'?'Change in modeled risk as the assumption changes.':'Actual observations over time. The vertical axis is auto-scaled; compare the values, not the slope.'} {groups.length>1?'Gaps mean no observation; points are not interpolated.':''} Focus the chart and use ← → to inspect values.</p>
 <details><summary>{title} — data table</summary><div className="tableScroll"><table><thead><tr><th>Observation / assumption</th><th>{unit}</th></tr></thead><tbody>{valid.map((p,i)=><tr key={i}><td>{time(p)}</td><td>{number(p.value)}</td></tr>)}</tbody></table></div></details></figure>;
}
