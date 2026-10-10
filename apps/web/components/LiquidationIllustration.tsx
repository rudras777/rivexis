import type {CSSProperties} from "react";
import {sampleSnapshot} from "../../../supabase/functions/rivexis-api/defi-sample.mjs";
import {metrics,format,WAD} from "../../../supabase/functions/rivexis-api/defi-model.mjs";

export function LiquidationIllustration(){
  const position=sampleSnapshot(0).positions[0];
  const collateral=position.reserves.find(reserve=>reserve.collateralEnabled)!;
  const baseline=BigInt(metrics(position).healthFactorRaw!);
  const stressed=BigInt(metrics(position,{[collateral.asset.toLowerCase()]:-2000}).healthFactorRaw!);
  const step=WAD/10n;
  const lower=[WAD,baseline,stressed].reduce((a,b)=>a<b?a:b);
  const upper=[WAD,baseline,stressed].reduce((a,b)=>a>b?a:b);
  const minimum=lower>WAD/5n?lower/step*step-WAD/5n:0n;
  const maximum=(upper+step-1n)/step*step+step;
  const at=(value:bigint)=>`${Number((value-minimum)*1_000_000n/(maximum-minimum))/10_000}%`;
  const axis={"--threshold-at":at(WAD),"--baseline-at":at(baseline),"--scenario-at":at(stressed)} as CSSProperties;
  const baseLabel=format(baseline,18,3),scenarioLabel=format(stressed,18,3);
  return <figure className="thresholdPlate">
    <figcaption>ILLUSTRATIVE AAVE POSITION / NOT LIVE DATA</figcaption>
    <div className="thresholdHeadline"><span>Baseline health</span><strong>{baseLabel}</strong><span aria-hidden="true">→</span><strong>{scenarioLabel}</strong><span>After a 20% collateral price decrease</span></div>
    <div className="healthAxis" style={axis} role="img" aria-label={`Illustrative health factor axis: liquidation threshold 1.000, baseline ${baseLabel}, scenario ${scenarioLabel}. Below 1.000 is liquidatable under these assumptions.`}>
      <div className="healthAxisTrack"><span className="healthAxisRisk"/>
        <span className="healthAxisMark healthAxisBoundary"><span>HF = 1.000</span></span>
        <span className="healthAxisMark healthAxisBaseline"><span>Baseline · {baseLabel}</span></span>
        <span className="healthAxisMark healthAxisScenario"><span>Scenario · {scenarioLabel}</span></span>
      </div>
      <div className="healthAxisRange"><span>{format(minimum,18,3)}</span><span>{format(maximum,18,3)}</span></div>
    </div>
    <p>{format(collateral.collateralRaw,collateral.decimals,0)} {collateral.symbol} × ${format(collateral.priceRaw,8,0)} × {Number(collateral.ltBps)/100}% ÷ ${format(metrics(position).debtRaw,8,0)} debt.<br/>The scenario changes collateral price; debt stays constant.</p>
    <div className="evidenceLine"><span>Protocol-specific rounding</span><span>Fresh oracle checks</span><span>Visible unsupported states</span></div>
    <p className="illustrationEvidence">Health factors calculated by the workspace model. Hypothetical inputs; no live oracle or execution evidence.</p>
  </figure>;
}
