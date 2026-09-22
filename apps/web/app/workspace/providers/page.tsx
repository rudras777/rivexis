"use client";

import {useState} from "react";
import {useQuery} from "@tanstack/react-query";
import {api} from "@/lib/api";

type P={provider_id:string;status:string;configured:boolean;detail?:string;latency_ms?:number;chain_id?:number;block_number?:number};

export default function Providers(){
  const [chain,setChain]=useState("ethereum");
  const [deep,setDeep]=useState(false);
  const q=useQuery({queryKey:["providers",chain,deep],queryFn:()=>api<{chain:string;providers:P[]}>(`/api/v1/providers/status?chain=${encodeURIComponent(chain)}&deep=${deep}`)});
  return <>
    <div className="workspaceHeader"><div><h1>Provider Health</h1><p>Configuration and live network health are separate states. Deep probe performs a real JSON-RPC chain check for configured RPC providers.</p></div></div>
    <section className="panel">
      <div style={{display:"flex",gap:12,alignItems:"end",flexWrap:"wrap"}}>
        <label className="field" style={{maxWidth:260}}>Chain<select value={chain} onChange={e=>setChain(e.target.value)}><option value="ethereum">Ethereum</option><option value="base">Base</option><option value="arbitrum">Arbitrum</option><option value="optimism">Optimism</option><option value="polygon">Polygon</option></select></label>
        <button className="button" onClick={()=>setDeep(v=>!v)}>{deep?"Use configuration view":"Run deep RPC probe"}</button>
      </div>
    </section>
    <section className="panel"><div className="tableWrap"><table className="table"><thead><tr><th>Provider</th><th>Status</th><th>Configured</th><th>Latency</th><th>Block</th></tr></thead><tbody>{q.data?.providers.map(p=><tr key={p.provider_id}><td>{p.provider_id}</td><td>{p.status}</td><td>{p.configured?"Yes":"No"}</td><td>{p.latency_ms!=null?`${p.latency_ms} ms`:"—"}</td><td>{p.block_number??"—"}</td></tr>)}</tbody></table>{q.isLoading&&<p>Loading provider registry…</p>}{q.error&&<p className="error">API unavailable: {(q.error as Error).message}</p>}</div></section>
  </>;
}
