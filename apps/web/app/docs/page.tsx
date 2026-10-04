import Link from "next/link";
import {PublicNav} from "@/components/PublicNav";

const guides=[
  ["Platform","/platform","How Rivexis moves from attributed evidence to a governed decision record."],
  ["Blockchain intelligence","/blockchain-intelligence","Execution, contract, monitoring, entity and cross-chain evidence across B1–B5."],
  ["Crypto finance","/crypto-finance","Portfolio, protocol, position, yield and treasury analysis across F1–F5."],
  ["DeFi risk","/defi-risk","Protocol, liquidation, oracle, liquidity and strategy-risk interpretation."],
  ["Methodology","/methodology","Decision policy, uncertainty handling, evidence conflicts and the five outcome states."],
  ["Data & provenance","/data","Source attribution, freshness, missing evidence and why zero observations are not treated as proof."],
  ["Security","/security","Authentication, evidence integrity, least privilege and fail-closed controls."],
] as const;

const roleGuides=[
  ["Analysts","/solutions/analysts"],
  ["Funds","/solutions/funds"],
  ["Treasuries","/solutions/treasuries"],
  ["Individuals","/solutions/individual"],
] as const;

export default function Page(){return <><PublicNav/><main className="contentPage">
  <div className="eyebrow">Rivexis</div>
  <h1>Documentation</h1>
  <p style={{fontSize:20}}>Public product guidance for understanding what Rivexis analyzes, which evidence a decision depends on, and what the system refuses to infer when evidence is missing or conflicting.</p>

  <h2>Product guides</h2>
  <ul>
    {guides.map(([label,href,description])=><li key={href}><Link className="textLink" href={href}><strong>{label}</strong></Link> — {description}</li>)}
  </ul>

  <h2>How to read a Rivexis decision</h2>
  <p>Applicable analyses resolve to <strong>PROCEED</strong>, <strong>MODIFY</strong>, <strong>WAIT</strong>, <strong>AVOID</strong>, or <strong>UNKNOWN</strong>. The outcome is only the summary. The supporting record should also show source provenance, freshness, confidence, blockers, missing data, conflicts and safer alternatives where they exist.</p>
  <p><Link className="textLink" href="/methodology">Read the decision methodology →</Link></p>

  <h2>Guidance by operating role</h2>
  <p>{roleGuides.map(([label,href],index)=><span key={href}>{index>0?" · ":""}<Link className="textLink" href={href}>{label}</Link></span>)}</p>

  <h2>Commercial and engineering scope</h2>
  <p><Link className="textLink" href="/pricing">Pricing and packaging</Link> remain separate from analytical truth: provider cost, monitoring volume, reporting depth and enterprise controls can change commercial scope without changing evidence policy.</p>
  <p>This public documentation describes the product contract. Repository-level implementation notes and internal engineering documentation are not presented here as a public API reference, and Rivexis does not claim an API surface that has not been explicitly published.</p>
</main></>}
