import Link from "next/link";
import {PublicNav} from "@/components/PublicNav";
import {Brand} from "@/components/Brand";

const engines=[
  ["B1","Transaction Simulation","Execution traces, approvals, transfers and state changes before commitment.","Execution"],
  ["B2","Contract Security","Deterministic contract controls, proxy state and attributed security evidence.","Security"],
  ["B3","Threat & Monitoring","Change-aware on-chain, oracle, liquidity and protocol monitoring.","Monitoring"],
  ["B4","Entity & Fund Flow","Counterparties, capital movement and attribution-preserving intelligence.","Entities"],
  ["B5","Cross-Chain Route","Route safety, liquidity, dependencies, cost and execution complexity.","Routes"],
  ["F1","Portfolio & Exposure","Concentration, liquidity, valuation and portfolio risk contribution.","Portfolio"],
  ["F2","Protocol Risk","Smart-contract, economic, oracle, governance and dependency risk.","Protocols"],
  ["F3","Position & Liquidation","Health factor, liquidation distance and scenario sensitivity.","Positions"],
  ["F4","Yield & Strategy Risk","Sustainable return separated from incentives and embedded risk.","Yield"],
  ["F5","Treasury Scenarios","Allocation, concentration, liquidity and stressed-loss analysis.","Treasury"],
];

export default function Home(){return <><PublicNav/><main>
  <section className="hero">
    <div className="heroCopy"><div className="eyebrow"><span/>Decision intelligence for digital-asset risk</div><h1>Evidence before<br/><em>execution.</em></h1><p>Rivexis turns fragmented blockchain, market and protocol evidence into an explainable institutional decision—before capital or transactions are committed.</p><div className="heroActions"><Link className="button buttonLarge" href="/signup">Create workspace <span aria-hidden="true">↗</span></Link><Link className="ghost buttonLarge" href="/methodology">Review methodology</Link></div><div className="trustLine"><span>Evidence attributed</span><span>Conflicts preserved</span><span>Unknown stays unknown</span></div></div>
    <div className="decisionStage"><div className="stageGlow"/><div className="decisionCard" aria-label="Illustrative decision panel"><div className="cardTopline"><span>ILLUSTRATIVE ANALYSIS</span><span className="liveDot">CONTROLLED</span></div><div className="decisionHead"><div><small>RIVEXIS DECISION</small><h2>MODIFY</h2></div><span className="status">EVIDENCE COMPLETE</span></div><div className="riskGauge"><div className="gauge"><b>42</b><small>/100</small></div><div><span className="metricLabel">OVERALL RISK</span><b>Manageable with controls</b><p>Two material findings require remediation before execution.</p></div></div><div className="miniRows"><div><span>Data confidence</span><b>91%</b></div><div><span>Source consensus</span><b>Moderate</b></div><div><span>Evidence records</span><b>18</b></div></div><div className="decisionFoot"><span>POLICY RVE-04</span><span>NOT LIVE DATA</span></div></div></div>
  </section>
  <section className="signalStrip" aria-label="Rivexis operating principles"><div><b>10</b><span>Specialist engines</span></div><div><b>5</b><span>Decision outcomes</span></div><div><b>2</b><span>Intelligence domains</span></div><div><b>0</b><span>Fabricated signals</span></div></section>
  <section className="section engineSection"><div className="sectionHeader"><div><div className="eyebrow"><span/>Intelligence architecture</div><h2>Specialist analytics.<br/>One decision policy.</h2></div><p className="sectionLead">Every engine retains source attribution, freshness, confidence and disagreement. Rivexis combines the record only after the evidence survives deterministic integrity checks.</p></div><div className="domainLabels"><span>Blockchain &amp; execution</span><span>Finance &amp; DeFi</span></div><div className="engineGrid">{engines.map((e,index)=><article className="engineCard" key={e[0]}><div className="engineCardHead"><small>{e[0]}</small><span>{e[3]}</span></div><h3>{e[1]}</h3><p>{e[2]}</p><div className="engineRule"><span style={{width:`${48+(index%5)*9}%`}}/></div></article>)}</div></section>
  <section className="institutionalBand"><div><div className="eyebrow eyebrowLight"><span/>Built for accountable decisions</div><h2>Clear when evidence is strong.<br/>Honest when it is not.</h2></div><div className="principleGrid"><div><b>01</b><h3>Evidence first</h3><p>Provider claims never become Rivexis facts without attribution and normalization.</p></div><div><b>02</b><h3>Fail closed</h3><p>Missing, stale or conflicting evidence resolves to an explicit uncertainty state.</p></div><div><b>03</b><h3>Explain every outcome</h3><p>Risk, confidence, blockers and mitigations stay visible to the decision maker.</p></div></div></section>
  <section className="finalCta"><div><div className="eyebrow"><span/>Start with evidence</div><h2>Bring institutional discipline to your next digital-asset decision.</h2></div><div className="heroActions"><Link className="button buttonLarge" href="/signup">Open a workspace <span aria-hidden="true">↗</span></Link><Link className="ghost buttonLarge" href="/security">Review security</Link></div></section>
  </main><footer className="footer"><div><Brand/><span>Risk · Value · Execution · Analysis</span></div><p>Decision intelligence only. Rivexis does not autonomously execute transactions or manage assets.</p></footer></>}
