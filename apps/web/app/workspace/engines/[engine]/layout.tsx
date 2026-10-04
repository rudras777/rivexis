import type {ReactNode} from "react";

export default function EngineLayout({children}:{children:ReactNode}){
  return <>
    <div className="truthNotice" role="note" data-testid="engine-runtime-boundary">
      <b>Production evidence boundary.</b> Non-demo mode submits an evidence request; it does not guarantee that a provider is configured. The current Edge runtime returns <strong>UNKNOWN</strong> when verified provider evidence is unavailable. Replace any sample addresses with the real target you intend to assess before submitting a non-demo request.
    </div>
    {children}
  </>;
}
