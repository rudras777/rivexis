import Link from "next/link";

type BrandVariant="wordmark"|"lockup"|"rail";

const assets={
  wordmark:{src:"/brand/rivexis-wordmark.png",width:900,height:184},
  lockup:{src:"/brand/rivexis-lockup.png",width:1000,height:268},
  rail:{src:"/brand/rivexis-mark.png",width:384,height:342},
} as const;

export function Brand({variant="wordmark"}:{variant?:BrandVariant}){
  const asset=assets[variant];
  return <Link href="/" className={`brand brand-${variant}`} aria-label="Rivexis home">
    <img src={asset.src} width={asset.width} height={asset.height} alt="Rivexis"/>
    {variant==="rail"?<span className="brandRailCopy"><b>RIVEXIS</b><small>Risk · Value · Execution · Analysis</small></span>:null}
  </Link>;
}
