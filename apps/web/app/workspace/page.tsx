"use client";

import Link from "next/link";
import {useWorkspace} from "@/components/WorkspaceContext";

const engines=[['B1','Transaction Simulation'],['B2','Transaction & Contract Security'],['B3','Threat & Monitoring'],['B4','Entity & Fund Flow'],['B5','Cross-Chain Route'],['F1','Portfolio & Exposure'],['F2','Protocol Risk'],['F3','Position & Liquidation'],['F4','Yield & Strategy'],['F5','Treasury & Scenarios']];

export default function Workspace(){
  const {workspace}=useWorkspace();
  return <>
    <div className="workspaceHeader"><div><h1>Rivexis Workspace</h1><p>Evidence → specialist engines → decision policy → explanation.</p></div><span className="badge">{workspace.name} · {workspace.access_role}</span></div>
    <div className="metricGrid"><div className="metricCard"><small>Core engines</small><strong>10</strong></div><div className="metricCard"><small>Primary domains</small><strong>2</strong></div><div className="metricCard"><small>Decision states</small><strong>5</strong></div><div className="metricCard"><small>Provider-grounded paths</small><strong>10*</strong></div></div>
    <section className="panel"><h2>Specialist engines</h2><p className="sectionLead">Runs launched from this shell use <b>{workspace.name}</b> as the active workspace context. API authorization remains authoritative for every workspace-scoped resource.</p><div className="engineList">{engines.map(([id,n])=><Link href={`/workspace/engines/${id}`} className="engineLink" key={id}><b>{id} · {n}</b><span>Run a clearly labeled demonstration scenario or connect normalized provider evidence.</span></Link>)}</div></section>
    <div className="demoBanner" style={{marginTop:16}}>* All ten engines have non-demo provider-grounded or direct-state execution paths, but several remain PARTIAL without commercial credentials or protocol-native evidence. The UI does not fabricate connectivity or completeness.</div>
  </>;
}
