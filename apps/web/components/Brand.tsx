import Link from "next/link";
import {useId} from "react";
import {brandGeometry as g} from "./brand-geometry";

export function Brand({variant="wordmark"}:{variant?:"wordmark"|"lockup"|"rail"|"compact"}){
  const compact=variant==="compact",lockup=variant==="lockup";
  const id=useId().replace(/:/g,"");
  return <Link prefetch={false} href="/" className={`brand brand-${variant}`} aria-label="Rivexis home">
    <svg viewBox={compact?"0 0 160 160":`0 0 ${g.width} ${lockup?203:146}`} aria-hidden="true" focusable="false">
      {!compact&&<path fill="currentColor" d={g.wordmark}/>}
      <g transform={compact?"translate(17 15)":`translate(${g.markX} 4)`}>
        <defs>
          <linearGradient id={`${id}-ribbon`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="var(--soft)"/><stop offset=".5" stopColor="currentColor"/><stop offset="1" stopColor="var(--soft)"/></linearGradient>
          <linearGradient id={`${id}-weave`} x1="0" y1="1" x2="1" y2="0"><stop stopColor="var(--soft)"/><stop offset=".45" stopColor="currentColor"/><stop offset=".75" stopColor="currentColor"/><stop offset="1" stopColor="var(--soft)"/></linearGradient>
        </defs>
        {g.ribbons.map((d,i)=><path key={i} fill={i===0?"var(--soft)":`url(#${id}-${i===1?"ribbon":"weave"})`} d={d}/>)}
        <path fill="currentColor" opacity=".22" d={g.bridge}/>
      </g>
      {lockup&&<path fill="currentColor" opacity=".82" d={g.tagline}/>}
    </svg>
  </Link>;
}
