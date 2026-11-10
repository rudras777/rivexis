import Link from "next/link";
import {brandGeometry as g} from "./brand-geometry";

export function Brand({variant="wordmark"}:{variant?:"wordmark"|"lockup"|"rail"|"compact"}){
  const compact=variant==="compact",lockup=variant==="lockup";
  return <Link prefetch={false} href="/" className={`brand brand-${variant}`} aria-label="Rivexis home">
    <svg viewBox={compact?"0 0 160 160":`0 0 ${g.width} ${lockup?203:146}`} aria-hidden="true" focusable="false">
      {!compact&&<path fill="currentColor" d={g.wordmark}/>}
      <image href={g.artwork} x={compact?0:g.markX-8} y={compact?0:-9} width={compact?160:148} height={compact?160:148} preserveAspectRatio="xMidYMid meet"/>
      {lockup&&<path fill="currentColor" opacity=".82" d={g.tagline}/>}
    </svg>
  </Link>;
}
