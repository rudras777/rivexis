"use client";
import {useEffect} from "react";
import {useDeFi} from "./DeFiContext";
import Link from "next/link";
import {usePublicSession} from "./AuthActions";
import {Brand} from "./Brand";
import {ApiError} from "@/lib/api";
import {authHref} from "@/lib/auth-destination";
export function FeatureGate({children}:{children:React.ReactNode}){
  const q=usePublicSession(),guest=(!q.isPending&&!q.isError&&q.data?.authenticated===false)||(q.error instanceof ApiError&&q.error.status===401);
  const risk=useDeFi();
  useEffect(()=>{if(guest||q.data?.authenticated===false)risk.reset()},[guest,q.data?.authenticated,risk.reset]);
  if(q.data?.authenticated&&q.data.email_verified)return children;
  return <main className="formPage"><section className="formCard" aria-live="polite"><Brand variant="lockup"/>
    <h1>{q.isPending?"Verifying workspace access":guest?"Your intelligence workspace":"Workspace access unavailable"}</h1>
    <p>{q.isPending?"Checking your existing secure session.":guest?"Live analysis, transaction previews and private reports require a free verified account.":"Rivexis could not confirm a verified session. No financial workflow has been opened."}</p>
    {!q.isPending&&<div className="gateActions">{guest?<><Link className="button" href={authHref("/signup","/app")}>Create free account</Link><Link className="ghost" href={authHref("/login","/app")}>Log in</Link></>:<button className="button" type="button" onClick={()=>void q.refetch()}>Retry access check</button>}<Link href="/demo" className="textButton">Explore the educational demo →</Link></div>}
  </section></main>;
}
