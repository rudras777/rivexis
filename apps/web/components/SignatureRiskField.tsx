"use client";
import {useEffect,useRef,useState,type CSSProperties,type PointerEvent} from "react";
import type {AtlasRenderer} from "@/lib/risk-atlas-renderer";
const chapters=['Exposure','Position','Boundary','Transaction','Alternatives','Evidence'] as const;
const contours=Array.from({length:14},(_,row)=>Array.from({length:41},(_,i)=>{
  const x=i*20,y=30+row*17+Math.sin(i/40*Math.PI*1.4)*(14-row)*5;
  return `${i?'L':'M'}${x.toFixed(1)} ${y.toFixed(1)}`;
}).join(' '));
export function SignatureRiskField(){
 const ref=useRef<HTMLElement>(null),frame=useRef(0),enabled=useRef(false);
 const canvas=useRef<HTMLCanvasElement>(null),renderer=useRef<AtlasRenderer|null>(null),pausedRef=useRef(false);
 const [ready,setReady]=useState(false),[paused,setPaused]=useState(false),[chapter,setChapter]=useState(0);
 useEffect(()=>{
  const target=canvas.current,home=ref.current?.closest('main');if(!target||!home)return;
  let alive=true,visible=true,scrollFrame=0,manual=false,loading=false,graphicsFailed=false;
  const media=matchMedia('(min-width:760px) and (prefers-reduced-motion:no-preference) and (forced-colors:none)');
  const connection=(navigator as Navigator&{connection?:{saveData?:boolean}}).connection;
  const eligible=()=>media.matches&&document.documentElement.dataset.motion!=='reduce'&&!connection?.saveData&&(navigator.hardwareConcurrency||4)>2;
  function scrollChapter(){scrollFrame=0;if(!alive)return;const sections=[home!.querySelector('.continuousHero'),home!.querySelector('.claritySection'),home!.querySelector('.liquidationShowcase'),home!.querySelector('.gasShowcase'),home!.querySelector('.defenseShowcase'),home!.querySelector('.methodologyFolio')];let next=0;for(let i=0;i<sections.length;i++)if((sections[i]?.getBoundingClientRect().top??Infinity)<innerHeight*.5)next=i;if(!manual){setChapter(next);renderer.current?.chapter(next,next>0)}home!.setAttribute('data-atlas-chapter',String(next));}
  const scroll=()=>{if(!scrollFrame)scrollFrame=requestAnimationFrame(scrollChapter)};
  const scrollIntent=()=>{manual=false};
  const scrollKey=(event:KeyboardEvent)=>{if(['PageDown','PageUp','Home','End','ArrowDown','ArrowUp'].includes(event.key))manual=false};
  window.addEventListener('wheel',scrollIntent,{passive:true});window.addEventListener('touchstart',scrollIntent,{passive:true});window.addEventListener('keydown',scrollKey);
  async function update(){
   if(!eligible()||graphicsFailed){renderer.current?.destroy();renderer.current=null;setReady(false);home!.setAttribute('data-atlas-motion','static');return;}
   if(!renderer.current&&!loading){loading=true;try{const module=await import('@/lib/risk-atlas-renderer');if(!alive||!eligible())return;renderer.current=module.createRiskAtlas(target!,()=>{if(alive)setReady(true)});}catch{if(alive)setReady(false)}finally{loading=false}}
   renderer.current?.motion(!pausedRef.current);renderer.current?.active(visible&&!document.hidden);home!.setAttribute('data-atlas-motion',!renderer.current?'static':pausedRef.current?'paused':'running');scrollChapter();
  }
  const observer=new IntersectionObserver(entries=>{visible=entries[0]?.isIntersecting??false;renderer.current?.active(visible&&!document.hidden);if(visible)void update()});observer.observe(home);
  const pointer=(event:globalThis.PointerEvent)=>{if(!enabled.current||pausedRef.current||event.pointerType!=='mouse')return;renderer.current?.pointer((event.clientX/innerWidth-.5)*2,(event.clientY/innerHeight-.5)*2)};
  const rest=()=>renderer.current?.pointer(0,0);
  const visibility=()=>renderer.current?.active(visible&&!document.hidden);
  const lost=(event:Event)=>{event.preventDefault();graphicsFailed=true;target!.removeEventListener('webglcontextlost',lost);renderer.current?.destroy();renderer.current=null;setReady(false);home!.setAttribute('data-atlas-motion','static')};
  const select=(event:Event)=>{manual=true;const value=(event as CustomEvent<number>).detail;renderer.current?.chapter(value,false)};
  home.addEventListener('pointermove',pointer,{passive:true});home.addEventListener('pointerleave',rest);window.addEventListener('scroll',scroll,{passive:true});window.addEventListener('rivexis-appearance-change',update);window.addEventListener('rivexis-atlas-motion',update);window.addEventListener('rivexis-atlas-chapter',select);document.addEventListener('visibilitychange',visibility);target.addEventListener('webglcontextlost',lost);media.addEventListener('change',update);void update();
  return()=>{alive=false;observer.disconnect();cancelAnimationFrame(scrollFrame);home.removeEventListener('pointermove',pointer);home.removeEventListener('pointerleave',rest);window.removeEventListener('scroll',scroll);window.removeEventListener('wheel',scrollIntent);window.removeEventListener('touchstart',scrollIntent);window.removeEventListener('keydown',scrollKey);window.removeEventListener('rivexis-appearance-change',update);window.removeEventListener('rivexis-atlas-motion',update);window.removeEventListener('rivexis-atlas-chapter',select);document.removeEventListener('visibilitychange',visibility);target.removeEventListener('webglcontextlost',lost);media.removeEventListener('change',update);renderer.current?.destroy();renderer.current=null;home.removeAttribute('data-atlas-motion');home.removeAttribute('data-atlas-chapter')};
 },[]);
 function pause(){const next=!paused;pausedRef.current=next;setPaused(next);window.dispatchEvent(new Event('rivexis-atlas-motion'));rest()}
 function selectChapter(value:number){setChapter(value);window.dispatchEvent(new CustomEvent('rivexis-atlas-chapter',{detail:value}))}
 useEffect(()=>{const media=matchMedia('(hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference) and (forced-colors:none)');const update=()=>{enabled.current=media.matches&&document.documentElement.dataset.motion!=='reduce';if(!enabled.current){cancelAnimationFrame(frame.current);ref.current?.style.removeProperty('--field-x');ref.current?.style.removeProperty('--field-y')}};update();media.addEventListener('change',update);window.addEventListener('rivexis-appearance-change',update);return()=>{media.removeEventListener('change',update);window.removeEventListener('rivexis-appearance-change',update);cancelAnimationFrame(frame.current)}},[]);
 function move(e:PointerEvent<HTMLElement>){if(!enabled.current||pausedRef.current||e.pointerType!=='mouse')return;const box=e.currentTarget.getBoundingClientRect(),x=(e.clientX-box.left)/box.width-.5,y=(e.clientY-box.top)/box.height-.5;cancelAnimationFrame(frame.current);frame.current=requestAnimationFrame(()=>{ref.current?.style.setProperty('--field-x',`${x*5}deg`);ref.current?.style.setProperty('--field-y',`${y*4}deg`)});}
 function rest(){cancelAnimationFrame(frame.current);ref.current?.style.removeProperty('--field-x');ref.current?.style.removeProperty('--field-y');}
 return <figure ref={ref} className="signatureRiskField riskAtlas" data-graphics={ready?'webgl':'vector'} data-view={chapters[chapter].toLowerCase()} onPointerMove={move} onPointerLeave={rest} aria-label="Conceptual three-dimensional risk field: exposure layers meet a visible boundary. No live financial data.">
  <canvas ref={canvas} className="atlasEnvironment" aria-hidden="true"/>
  <div className="riskFieldScene" aria-hidden="true"><div className="riskFieldModel">{[0,1,2,3,4].map(i=><svg key={i} className="riskFieldPlane" viewBox="0 0 800 300" style={{'--depth':`${(i-2)*22}px`,'--plane-alpha':.3+i*.13} as CSSProperties}><g fill="none" stroke="currentColor" strokeWidth=".8">{contours.map((d,j)=><path d={d} key={j}/>)}{Array.from({length:17},(_,j)=><path key={j} d={`M${j*50} 30L${j*50} 290`} opacity=".25"/>)}<path d="M20 165C220 65 440 260 780 125" stroke="var(--bronze)" strokeWidth="1.5"/></g><path d="M20 165C220 65 440 260 780 125L780 290H20Z" fill="currentColor" opacity=".035"/></svg>)}<span className="fieldAxis fieldAxisA"/><span className="fieldAxis fieldAxisB"/></div></div>
  <svg className="atlasVectorPaths" viewBox="0 0 800 300" aria-hidden="true"><g fill="none" stroke="var(--soft)" strokeWidth="3">{(chapter===4?[-1,0,1]:chapter===3?[0]:[]).map(branch=><path key={branch} d={`M80 160C280 150 430 ${160+branch*60} 720 ${160+branch*90}`}/>)}</g>{chapter===3&&[120,310,500,690].map(x=><circle key={x} cx={x} cy="160" r="5" fill="var(--bronze)"/>)}</svg>
  <figcaption><span>EXPOSURE</span><span>BOUNDARY</span><span>RESPONSE</span></figcaption><p>Conceptual risk field · Financial analysis begins inside your account.</p>
  <div className="atlasControls" aria-label="Conceptual Risk Atlas views">{[0,2,3,4].map(value=><button key={value} type="button" aria-pressed={chapter===value} onClick={()=>selectChapter(value)}>{chapters[value]}</button>)}<button type="button" disabled={!ready} aria-pressed={paused} onClick={pause}>{!ready?'Static view':paused?'Resume motion':'Pause motion'}</button></div>
  <p className="atlasDescription">{chapter===3?'A proposed action meets balances, allowances and position constraints.':chapter===4?'Available capital creates different paths, each with remaining modeled risk.':chapter===2?'The boundary is conditional: a change in collateral can change the position.':'One landscape of connected exposure. Geometry is illustrative, never a financial result.'}</p>
 </figure>;
}
