"use client";
import {useEffect,useRef,type CSSProperties,type PointerEvent} from "react";
const contours=Array.from({length:14},(_,row)=>Array.from({length:41},(_,i)=>{
  const x=i*20,y=30+row*17+Math.sin(i/40*Math.PI*1.4)*(14-row)*5;
  return `${i?'L':'M'}${x.toFixed(1)} ${y.toFixed(1)}`;
}).join(' '));
export function SignatureRiskField(){
 const ref=useRef<HTMLElement>(null),frame=useRef(0),enabled=useRef(false);
 useEffect(()=>{const media=matchMedia('(hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference) and (forced-colors:none)');const update=()=>{enabled.current=media.matches;if(!media.matches){cancelAnimationFrame(frame.current);ref.current?.style.removeProperty('--field-x');ref.current?.style.removeProperty('--field-y')}};update();media.addEventListener('change',update);return()=>{media.removeEventListener('change',update);cancelAnimationFrame(frame.current)}},[]);
 function move(e:PointerEvent<HTMLElement>){if(!enabled.current||e.pointerType!=='mouse')return;const box=e.currentTarget.getBoundingClientRect(),x=(e.clientX-box.left)/box.width-.5,y=(e.clientY-box.top)/box.height-.5;cancelAnimationFrame(frame.current);frame.current=requestAnimationFrame(()=>{ref.current?.style.setProperty('--field-x',`${x*5}deg`);ref.current?.style.setProperty('--field-y',`${y*4}deg`)});}
 function rest(){cancelAnimationFrame(frame.current);ref.current?.style.removeProperty('--field-x');ref.current?.style.removeProperty('--field-y');}
 return <figure ref={ref} className="signatureRiskField" onPointerMove={move} onPointerLeave={rest} aria-label="Conceptual three-dimensional risk field: exposure layers meet a visible boundary. No live financial data.">
  <div className="riskFieldScene" aria-hidden="true"><div className="riskFieldModel">{[0,1,2,3,4].map(i=><svg key={i} className="riskFieldPlane" viewBox="0 0 800 300" style={{'--depth':`${(i-2)*22}px`,'--plane-alpha':.3+i*.13} as CSSProperties}><g fill="none" stroke="currentColor" strokeWidth=".8">{contours.map((d,j)=><path d={d} key={j}/>)}{Array.from({length:17},(_,j)=><path key={j} d={`M${j*50} 30L${j*50} 290`} opacity=".25"/>)}<path d="M20 165C220 65 440 260 780 125" stroke="var(--bronze)" strokeWidth="1.5"/></g><path d="M20 165C220 65 440 260 780 125L780 290H20Z" fill="currentColor" opacity=".035"/></svg>)}<span className="fieldAxis fieldAxisA"/><span className="fieldAxis fieldAxisB"/></div></div>
  <figcaption><span>EXPOSURE</span><span>BOUNDARY</span><span>RESPONSE</span></figcaption><p>Conceptual risk field · Financial analysis begins inside your free account.</p>
 </figure>;
}
