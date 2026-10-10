"use client";
import {useEffect,useRef} from "react";
import {usePathname} from "next/navigation";
export function PrecisionInteractions(){
 const pointer=useRef<HTMLDivElement>(null),path=usePathname();
 useEffect(()=>{
  const media=matchMedia('(hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference) and (forced-colors:none)');let frame=0;
  const hide=()=>{cancelAnimationFrame(frame);pointer.current?.removeAttribute('data-active')};
  const move=(e:PointerEvent)=>{const target=e.target instanceof Element?e.target:null;if(!media.matches||e.pointerType!=='mouse'||!target?.closest('.institutionalHome,.folioNav,.authEntry')||!target.closest('a,button,summary')){hide();return}cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{const p=pointer.current;if(p){p.style.transform=`translate3d(${e.clientX+12}px,${e.clientY+12}px,0)`;p.dataset.active='true'}})};
  document.addEventListener('pointermove',move,{passive:true});document.addEventListener('pointerleave',hide);window.addEventListener('blur',hide);window.addEventListener('scroll',hide,{passive:true});media.addEventListener('change',hide);
  return()=>{hide();document.removeEventListener('pointermove',move);document.removeEventListener('pointerleave',hide);window.removeEventListener('blur',hide);window.removeEventListener('scroll',hide);media.removeEventListener('change',hide)};
 },[path]);
 return <div ref={pointer} className="precisionPointer" aria-hidden="true"/>;
}
