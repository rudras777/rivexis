"use client";
import {useEffect,useRef,useState} from 'react';
import {usePathname} from 'next/navigation';
// Deterministic strands keep the server render and hydration identical. Three
// separate current families create depth without restoring the old grid sheet.
const strands=Array.from({length:12},(_,i)=>[
 `M-100 ${475+i*12} C140 ${405+i*9} 240 ${480+i*7} 470 ${645+i*5} S850 ${770-i*5} 1300 ${470+i*14}`,
 `M-100 ${670+i*10} C180 ${530+i*7} 300 ${560+i*9} 575 ${715+i*3} S920 ${570+i*10} 1300 ${600+i*11}`,
 `M-100 ${310+i*13} C140 ${325+i*14} 180 ${490+i*7} 440 ${565+i*7} S860 ${735-i*7} 1300 ${390+i*16}`,
]).flat();
const particles=Array.from({length:72},(_,i)=>({x:(i*137+53)%1260-30,y:570+((i*73)%220),r:i%13===0?3.5:.6+(i%3)*.3}));
const signals=[strands[4],strands[19],strands[29]];
const nodes=[[46,459],[87,541],[133,504],[184,477],[235,534],[279,568],[336,594],[386,623],[453,656],[513,691],[597,706],[663,683],[726,664],[795,635],[841,607],[898,578],[951,549],[1016,505],[1072,477],[1143,433],[1204,492],[90,369],[197,439],[354,548],[1009,632],[1103,587],[728,742],[1167,684]];
export function BlockchainBackground(){
 const path=usePathname(),ref=useRef<HTMLDivElement>(null),[paused,setPaused]=useState(false),[allowed,setAllowed]=useState(false),[visible,setVisible]=useState(true);
 useEffect(()=>{const media=matchMedia('(prefers-reduced-motion:no-preference) and (forced-colors:none)');const update=()=>{setAllowed(media.matches&&document.documentElement.dataset.motion!=='reduce'&&!(navigator as Navigator&{connection?:{saveData?:boolean}}).connection?.saveData&&(navigator.hardwareConcurrency||4)>2);setVisible(!document.hidden)};media.addEventListener('change',update);document.addEventListener('visibilitychange',update);window.addEventListener('rivexis-appearance-change',update);update();return()=>{media.removeEventListener('change',update);document.removeEventListener('visibilitychange',update);window.removeEventListener('rivexis-appearance-change',update)}},[]);
 const context=path.includes('/settings')?'settings':path.startsWith('/workspace')?'workspace':/\/(login|signup|verify-email|forgot-password|reset-password)/.test(path)?'auth':'public';
 return <><div ref={ref} className="blockchainBackground" aria-hidden="true" data-context={context} data-moving={allowed&&!paused&&visible}>
  <div className="blockchainAtmosphere"/><div className="blockchainDepth"><svg className="blockchainLines" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice"><g fill="none" strokeWidth=".65">{strands.map((d,i)=><path key={d} d={d} stroke={i%9===4?'var(--bronze)':'var(--soft)'} opacity={i%3===2?.15:.25+(i%4)*.055}/>)}</g><g fill="none" stroke="var(--bronze)" strokeWidth="1.2">{signals.map((d,i)=><path key={d} d={d} className={`blockchainSignal signal${i}`} pathLength="1000" strokeDasharray="2 998"/>)}</g><g className="ledgerParticles" fill="var(--soft)">{particles.map((p,i)=><circle key={i} cx={p.x} cy={p.y} r={p.r} opacity={i%13===0?.12:.25+(i%4)*.1}/>)}</g><g>{nodes.map(([x,y],i)=><g key={x} className={`blockchainNode node${i%3}`}><circle cx={x} cy={y} r={i%5===0?10:5} fill={i%5===0?'var(--bronze)':'var(--soft)'} opacity=".14"/><circle cx={x} cy={y} r={i%5===0?2:1.1} fill={i%5===0?'var(--bronze)':'var(--soft)'}/>{i%5===0&&<path d={`M${x-9} ${y}h18M${x} ${y-34}v43`} stroke="var(--bronze)" strokeWidth=".5" opacity=".5"/>}</g>)}</g></svg>
  {[0,1,2,3,4].map(i=><div className={`blockchainCube cube${i}`} key={i}><i className="cubeHalo"/><i className="cubeCore"/>{['front','back','left','right','top','bottom'].map(face=><span className={`${face}Face`} key={face}/>)}</div>)}</div>
 </div><button className="backgroundMotionButton" type="button" aria-label={!allowed?'Background motion disabled':paused?'Resume background motion':'Pause background motion'} aria-pressed={paused} disabled={!allowed} onClick={()=>setPaused(!paused)} title={!allowed?'Your accessibility or device preferences use a static background':paused?'Resume background motion':'Pause background motion'}><span aria-hidden="true">{paused||!allowed?'Ã¢â€“Â·':'Ã¢â€¦Â¡'}</span></button></>;
}
