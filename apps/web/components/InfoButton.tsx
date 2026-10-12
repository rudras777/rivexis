"use client";
import {useEffect,useLayoutEffect,useId,useRef,useState} from 'react';
export function InfoButton({label,children}:{label:string;children:React.ReactNode}){
 const id=useId(),root=useRef<HTMLSpanElement>(null),tooltip=useRef<HTMLSpanElement>(null),[open,setOpen]=useState(false),[pinned,setPinned]=useState(false);
 useEffect(()=>{if(!pinned)return;const close=(e:PointerEvent)=>{if(!root.current?.contains(e.target as Node)){setOpen(false);setPinned(false)}};document.addEventListener('pointerdown',close);return()=>document.removeEventListener('pointerdown',close)},[pinned]);
 useLayoutEffect(()=>{if(!open)return;const position=()=>{if(!root.current||!tooltip.current)return;const box=root.current.getBoundingClientRect(),tip=tooltip.current,rect=tip.getBoundingClientRect();tip.style.left=`${Math.max(12,Math.min(box.left,innerWidth-rect.width-12))}px`;tip.style.top=`${box.bottom+rect.height+12<innerHeight?box.bottom+6:Math.max(12,box.top-rect.height-6)}px`};position();window.addEventListener("resize",position);window.addEventListener("scroll",position,true);return()=>{window.removeEventListener("resize",position);window.removeEventListener("scroll",position,true)}},[open]);
 return <span className="infoControl" ref={root} onMouseEnter={()=>setOpen(true)} onMouseLeave={()=>{if(!pinned)setOpen(false)}} onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);setPinned(false);e.stopPropagation()}}}>
  <button type="button" className="infoButton" aria-label={`About ${label}`} aria-expanded={open} aria-controls={id} aria-describedby={open?id:undefined} onFocus={()=>setOpen(true)} onBlur={()=>{if(!pinned)setOpen(false)}} onClick={()=>{setPinned(!pinned);setOpen(!pinned)}}><span aria-hidden="true">ⓘ</span></button>
  <span ref={tooltip} className="infoTooltip" id={id} role="tooltip" hidden={!open}>{children}</span>
 </span>;
}
