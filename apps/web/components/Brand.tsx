import Link from "next/link";
import {brandGeometry as g} from "./brand-geometry";

export function Brand({variant="wordmark"}:{variant?:"wordmark"|"lockup"|"rail"|"compact"}){
  const compact=variant==="compact",lockup=variant==="lockup";
  return <Link href="/" className={`brand brand-${variant}`} aria-label="Rivexis home">
    <svg viewBox={compact?"0 0 160 160":`0 0 ${g.width} ${lockup?203:146}`} aria-hidden="true" focusable="false">
      {!compact&&<path fill="currentColor" d={g.wordmark}/>}
      <g transform={compact?"translate(20 17)":`translate(${g.markX} 4)`}>
        {g.ribbons.map((d,i)=><path key={i} fill="var(--soft)" d={d}/>)}
        <path fill="currentColor" d={g.bridge}/>
      </g>
      {lockup&&<path fill="currentColor" opacity=".82" d={g.tagline}/>}
    </svg>
  </Link>;
}
