"use client";

import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect,useRef,type MouseEvent} from "react";

const primaryItems=[
  ["Intelligence","/platform"],
  ["LiquidationGuard","/liquidationguard"],
  ["GasGuard","/gasguard"],
  ["Methodology","/methodology"],
] as const;
const mobileItems=[...primaryItems,["Defense Frontier","/defense-frontier"],["Educational demo","/demo"]] as const;

export function PublicNavigation(){
  const path=usePathname();
  const menu=useRef<HTMLDetailsElement>(null);
  const trigger=useRef<HTMLElement>(null);

  useEffect(()=>{if(menu.current)menu.current.open=false},[path]);
  useEffect(()=>{
    const dismiss=(event:PointerEvent)=>{
      if(menu.current?.open&&!menu.current.contains(event.target as Node))menu.current.open=false;
    };
    document.addEventListener("pointerdown",dismiss);
    return()=>document.removeEventListener("pointerdown",dismiss);
  },[]);

  function select(event:MouseEvent<HTMLAnchorElement>){
    if(event.button===0&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey&&menu.current)menu.current.open=false;
  }

  return <>
    <nav className="desktopPublicNav" aria-label="Primary navigation">
      {primaryItems.map(([label,href])=><Link key={href} href={href} aria-current={path===href?"page":undefined}>{label}</Link>)}
    </nav>
    <details className="mobileNav" ref={menu} onKeyDown={event=>{
      if(event.key==="Escape"&&menu.current?.open){
        menu.current.open=false;
        trigger.current?.focus();
        event.stopPropagation();
      }
    }}>
      <summary ref={trigger} aria-label="Menu — open navigation">Menu <svg aria-hidden="true" viewBox="0 0 12 12" width="12" height="12"><path d="m3 4.5 3 3 3-3" fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></summary>
      <nav aria-label="Mobile navigation">
        {mobileItems.map(([label,href])=><Link key={href} href={href} onClick={select} aria-current={path===href?"page":undefined}>{label}</Link>)}
      </nav>
    </details>
  </>;
}
