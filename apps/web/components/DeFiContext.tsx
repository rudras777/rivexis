"use client";
import {createContext,useContext,useState,useCallback,type ReactNode} from "react";
import type {Snapshot,Frontier} from "../../../supabase/functions/rivexis-api/defi-model.mjs";
type State={reset:()=>void;snapshot:Snapshot|null;previousSnapshot:Snapshot|null;setSnapshot:(s:Snapshot|null)=>void;shocks:Record<string,number>;setShocks:(s:Record<string,number>)=>void;budget:string;setBudget:(s:string)=>void;target:string;setTarget:(s:string)=>void;fee:string;setFee:(s:string)=>void;objective:string;setObjective:(s:string)=>void;result:Frontier|null;setResult:(s:Frontier|null)=>void};
const Context=createContext<State|null>(null);
export function DeFiProvider({children}:{children:ReactNode}){
  const [snapshot,setSnapshotState]=useState<Snapshot|null>(null),[previousSnapshot,setPreviousSnapshot]=useState<Snapshot|null>(null),[shocks,setShocks]=useState<Record<string,number>>({}),[budget,setBudget]=useState("3000"),[target,setTarget]=useState("1.50"),[fee,setFee]=useState("25"),[objective,setObjective]=useState("target"),[result,setResult]=useState<Frontier|null>(null);
  const reset=useCallback(()=>{setSnapshotState(null);setPreviousSnapshot(null);setShocks({});setBudget("3000");setTarget("1.50");setFee("25");setObjective("target");setResult(null)},[]);
  function setSnapshot(next:Snapshot|null){setPreviousSnapshot(snapshot&&next&&snapshot.wallet===next.wallet&&!next.sample?snapshot:null);setSnapshotState(next)}
  return <Context.Provider value={{reset,snapshot,previousSnapshot,setSnapshot,shocks,setShocks,budget,setBudget,target,setTarget,fee,setFee,objective,setObjective,result,setResult}}>{children}</Context.Provider>;
}
export function useDeFi(){const c=useContext(Context);if(!c)throw new Error("DeFi provider missing");return c}
