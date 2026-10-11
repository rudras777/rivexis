"use client";
import {createContext,useContext,useState,useCallback,useEffect,useRef,type ReactNode} from "react";
import {useAccountPreferences} from "./AccountPreferences";
import type {Snapshot,Frontier,Action} from "../../../supabase/functions/rivexis-api/defi-model.mjs";
type State={draftTransaction:Action|null;setDraftTransaction:(s:Action|null)=>void;selectedAlternative:number;setSelectedAlternative:(i:number)=>void;reset:()=>void;snapshot:Snapshot|null;previousSnapshot:Snapshot|null;setSnapshot:(s:Snapshot|null)=>void;shocks:Record<string,number>;setShocks:(s:Record<string,number>)=>void;budget:string;setBudget:(s:string)=>void;target:string;setTarget:(s:string)=>void;fee:string;setFee:(s:string)=>void;objective:string;setObjective:(s:string)=>void;result:Frontier|null;setResult:(s:Frontier|null)=>void};
const Context=createContext<State|null>(null);
export function DeFiProvider({children}:{children:ReactNode}){
  const {preferences}=useAccountPreferences();const defaults=useRef(preferences);defaults.current=preferences;
  const [snapshot,setSnapshotState]=useState<Snapshot|null>(null),[previousSnapshot,setPreviousSnapshot]=useState<Snapshot|null>(null),[shocks,setShocks]=useState<Record<string,number>>({}),[budget,setBudget]=useState("3000"),[target,setTarget]=useState("1.50"),[fee,setFee]=useState("25"),[objective,setObjective]=useState("target"),[result,setResult]=useState<Frontier|null>(null);
  const [draftTransaction,setDraftTransaction]=useState<Action|null>(null),[selectedAlternative,setSelectedAlternative]=useState(0);
  const reset=useCallback(()=>{setSnapshotState(null);setPreviousSnapshot(null);setShocks({});setBudget(defaults.current.defaultBudget);setTarget(defaults.current.defaultTarget);setFee(defaults.current.defaultFee);setObjective(defaults.current.defaultObjective);setResult(null);setDraftTransaction(null);setSelectedAlternative(0)},[]);
  useEffect(()=>{if(!snapshot&&!result){setBudget(preferences.defaultBudget);setTarget(preferences.defaultTarget);setFee(preferences.defaultFee);setObjective(preferences.defaultObjective)}},[preferences.defaultBudget,preferences.defaultTarget,preferences.defaultFee,preferences.defaultObjective]);
  function setSnapshot(next:Snapshot|null){setPreviousSnapshot(snapshot&&next&&snapshot.wallet===next.wallet&&!next.sample?snapshot:null);setSnapshotState(next)}
  return <Context.Provider value={{draftTransaction,setDraftTransaction,selectedAlternative,setSelectedAlternative,reset,snapshot,previousSnapshot,setSnapshot,shocks,setShocks,budget,setBudget,target,setTarget,fee,setFee,objective,setObjective,result,setResult}}>{children}</Context.Provider>;
}
export function useDeFi(){const c=useContext(Context);if(!c)throw new Error("DeFi provider missing");return c}
