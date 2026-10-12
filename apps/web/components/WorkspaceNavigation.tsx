"use client";
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {useEffect,useRef,useState} from 'react';
export const workspaceGroups=[
 {name:'Risk Intelligence',items:[['LiquidationGuard','/workspace','Observed lending exposure'],['Stress Testing','/workspace/scenarios','Explicit market assumptions'],['Risk Reports','/workspace/reports','Private evidence receipts']]},
 {name:'Transaction Intelligence',items:[['GasGuard','/workspace/transactions','Supported call and fee assessment']]},
 {name:'Decision Intelligence',items:[['Defense Planner','/workspace/frontier','Capital-constrained alternatives'],['Scenario Analysis','/workspace/scenarios','Sensitivity before a decision'],['Decision Reports','/workspace/reports','Reproducible comparisons']]},
 {name:'On-Chain',items:[['Wallets','/workspace/wallets','Providers and analysis addresses'],['Contracts','/workspace/contracts','Block-aware contract inspection'],['Networks','/workspace/networks','Supported network evidence']]},
 {name:'Research & Monitoring',items:[['Methodology','/methodology','Financial models and coverage'],['Monitoring & Reports','/workspace/reports','Bounded checks and history'],['Historical Records','/workspace/history','Retained account analyses']]},
] as const;
export function WorkspaceNavigation({mobile=false}:{mobile?:boolean}){
 const path=usePathname(),root=useRef<HTMLElement>(null),timer=useRef<ReturnType<typeof setTimeout>|null>(null),[open,setOpen]=useState<string|null>(null);
 const clear=()=>{if(timer.current)clearTimeout(timer.current)};
 useEffect(()=>{setOpen(null);clear()},[path]);
 useEffect(()=>{const outside=(e:PointerEvent)=>{if(!root.current?.contains(e.target as Node))setOpen(null)};document.addEventListener('pointerdown',outside);return()=>{clear();document.removeEventListener('pointerdown',outside)}},[]);
 const active=(name:string)=>path==='/workspace'?'Risk Intelligence'===name:path.includes('/frontier')?name==='Decision Intelligence':path.includes('/transactions')?name==='Transaction Intelligence':/\/(wallets|contracts|networks)$/.test(path)?name==='On-Chain':path.includes('/scenarios')?name==='Risk Intelligence':/\/(reports|history)$/.test(path)?name==='Research & Monitoring':false;
 return <nav ref={root} className={mobile?'workspaceGroupedMobile':'workspaceDesktopNav workspaceGroupedNav'} aria-label={mobile?'Mobile workspace':'Workspace'} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setOpen(null)}} onKeyDown={e=>{if(e.key==='Escape'){const name=open;setOpen(null);root.current?.querySelector<HTMLButtonElement>(`button[data-category="${name}"]`)?.focus();e.stopPropagation()}}}>
  <Link href="/workspace/overview" aria-current={path==='/workspace/overview'?'page':undefined}>Overview</Link>
  {workspaceGroups.map(group=><div key={group.name} className="workspaceNavGroup" onPointerEnter={e=>{clear();if(!mobile&&e.pointerType==='mouse')timer.current=setTimeout(()=>setOpen(group.name),140)}} onPointerLeave={e=>{clear();if(!mobile&&e.pointerType==='mouse')timer.current=setTimeout(()=>setOpen(null),260)}}>
   <button type="button" data-category={group.name} data-active={active(group.name)} aria-expanded={open===group.name} aria-controls={`${mobile?'mobile':'desktop'}-${group.name.replaceAll(' ','-')}`} onClick={()=>{clear();setOpen(open===group.name?null:group.name)}} onKeyDown={e=>{if(e.key==='ArrowDown'){e.preventDefault();setOpen(group.name);const trigger=e.currentTarget;requestAnimationFrame(()=>trigger.parentElement?.querySelector<HTMLAnchorElement>('a')?.focus())}}}>{group.name}<span aria-hidden="true">⌄</span></button>
   <div id={`${mobile?'mobile':'desktop'}-${group.name.replaceAll(' ','-')}`} className="workspaceDropdown" hidden={open!==group.name}>{group.items.map(([name,href,description])=><Link key={name} href={href} aria-label={name} aria-current={path===href?'page':undefined}><strong>{name}</strong><span>{description}</span></Link>)}</div>
  </div>)}
 </nav>;
}
