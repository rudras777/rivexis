"use client";
import {useState} from "react";
import {sampleSnapshot} from "../../../supabase/functions/rivexis-api/defi-sample.mjs";
import {scenario,format} from "../../../supabase/functions/rivexis-api/defi-model.mjs";
const example=sampleSnapshot(0);
const weth=example.positions[0].reserves[0].asset.toLowerCase();
const usd=(raw:string)=>"$"+format(raw,8,0).replace(/\B(?=(\d{3})+(?!\d))/g,",");
export function RiskFolio(){
  const [shock,setShock]=useState(-1000);
  const result=scenario(example,{[weth]:shock},[],0)[0];
  const health=format(result.healthFactorRaw!,18,3);
  // Floating point is used only for SVG coordinates, never model accounting.
  const x=52+388*(shock+4000)/6000,y=245-Number(result.healthFactorRaw!)/1e18*100;
  return <figure className="riskFolio"><figcaption><span className="folioIndex">RESEARCH FOLIO / 01</span><span>Illustrative position</span></figcaption>
    <div className="folioMetric"><div><span>Scenario health factor</span><output aria-live="polite" aria-label="Example health factor">{health}</output></div><div className="folioStatus"><span className="folioDot"/>{result.liquidatable?"Below modeled boundary":result.healthFactorRaw==="1000000000000000000"?"At modeled boundary":"Above modeled boundary"}</div></div>
    <svg viewBox="0 0 490 245" role="img" aria-label={`Hypothetical Aave health factor ${health} at a ${shock/100}% WETH price change. Liquidation boundary at 1.000.`}>
      <g fill="none" stroke="var(--border)"><path d="M52 52V190H440"/><path strokeDasharray="2 6" d="M52 85H440M52 115H440M52 165H440M149 52V190M246 52V190M343 52V190"/></g>
      <path d="M52 165L440 85L440 190H52Z" fill="var(--brand)" opacity=".10"/>
      <path d="M52 145H440" stroke="var(--bronze)" strokeDasharray="5 5"/>
      <path d="M52 165L440 85" fill="none" stroke="var(--soft)" strokeWidth="2.5"/>
      <path d={`M${x} ${y}V190`} stroke="var(--soft)" strokeDasharray="2 5"/>
      <circle cx={x} cy={y} r="13" fill="none" stroke="var(--soft)" opacity=".35"/><circle cx={x} cy={y} r="4.5" fill="var(--soft)"/>
      <g fill="var(--text-muted)" fontSize="11"><text x="52" y="32">HEALTH FACTOR</text><text x="320" y="136" fill="var(--bronze)">1.000 boundary</text><text x="52" y="212">−40%</text><text x="246" y="212" textAnchor="middle">PRICE CHANGE</text><text x="440" y="212" textAnchor="end">+20%</text></g>
    </svg>
    <label className="folioSlider">Example WETH price change <output>{shock>0?"+":""}{shock/100}%</output><input type="range" min="-4000" max="2000" step="100" value={shock} onChange={e=>setShock(Number(e.target.value))} aria-label="Example WETH price change"/></label>
    <div className="folioBalances"><div><span>Modeled collateral</span><b>{usd(result.collateralRaw)}</b></div><div><span>Debt, held constant</span><b>$18,000</b></div><div><span>Liquidation threshold</span><b>80%</b></div></div>
    <p className="folioDisclaimer">Hypothetical inputs: 10 WETH at $3,000, $18,000 USDC debt. Educational model only. No live wallet or transaction.</p>
  </figure>;
}
