import {sampleSnapshot} from "../../../supabase/functions/rivexis-api/defi-sample.mjs";
import {frontier,format} from "../../../supabase/functions/rivexis-api/defi-model.mjs";
export function DefenseIllustration(){
  const snapshot=sampleSnapshot(0),result=frontier(snapshot,{budget:"3000",gasReserve:"0",target:"1.50",shocks:{},objective:"target"},0),best=result.alternatives[0];
  return <figure className="defenseComparison productVisual defenseVisual">
    <figcaption><span>DEFENSE FRONTIER / EXAMPLE</span><span>Hypothetical inputs</span></figcaption>
    <div className="visualCanvas"><img className="featureDiagram" src="/diagrams/defense-branches.svg" width="600" height="720" loading="lazy" decoding="async" alt="Layered budget contours connect a current position with one modeled repayment alternative. The comparison panels retain the actual hypothetical model results and remaining constraints."/>
      <div className="comparisonColumns"><div className="compositionCard currentEvidence"><span className="comparisonLabel">Current position</span><strong>1.333</strong><span>Modeled health factor</span><p>$18,000 debt<br/>$30,000 collateral</p></div><div className="compositionCard alternativeEvidence"><span className="comparisonLabel">Alternative found</span><strong>{format(best.minHealthFactorRaw!,18,3)}</strong><span>Modeled health factor</span><p>Repay {format(best.actions[0].amountRaw,best.actions[0].decimals,0)} USDC<br/>Collateral held constant</p><span className="visualModelLabel">MODELED COMPARISON</span></div></div>
      <span className="visualMarginalia" aria-hidden="true">CAPITAL / CONSTRAINTS / REMAINING RISK</span>
    </div>
    <dl className="comparisonConstraints"><div><dt>Capital budget</dt><dd>$3,000</dd></div><div><dt>Capital allocated</dt><dd>${format(best.capitalRaw,8,0)}</dd></div><div><dt>Chosen target</dt><dd>1.500</dd></div></dl><p className="folioDisclaimer">Calculated by the canonical model with a 5% budget search and $0 assumed fees. Meets this modeled target; approval, real fees and execution remain unverified. No guarantee of safety.</p>
  </figure>;
}
