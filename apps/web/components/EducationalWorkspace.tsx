"use client";
import {useEffect,useRef,useState} from 'react';
import {AppShell} from './AppShell';
import {WorkspaceNavigation} from './WorkspaceNavigation';
import {DeFiProvider} from './DeFiContext';
import {DeFiWorkspace,type View} from './DeFiWorkspace';

const paths:Record<View,string>={portfolio:'/workspace',scenarios:'/workspace/scenarios',frontier:'/workspace/frontier',transactions:'/workspace/transactions',reports:'/workspace/reports'};

// The existing authenticated shell surrounds a separate educational analysis.
// Leaving this route restores the real analysis in the outer provider.
export function EducationalWorkspace(){
  const [view,setView]=useState<View>('portfolio');
  const previous=useRef(view);
  useEffect(()=>{if(previous.current===view)return;previous.current=view;document.getElementById('workspace-main')?.querySelector<HTMLHeadingElement>('h1')?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'auto'})},[view]);
  function select(href:string){const item=(Object.entries(paths) as [View,string][]).find(([,path])=>path===href);if(!item)return false;setView(item[0]);return true}
  return <AppShell renderNavigation={mobile=><WorkspaceNavigation mobile={mobile} activePath={paths[view]} onSelectDestination={select}/>}><DeFiProvider><DeFiWorkspace initialView={view} onViewChange={setView} demoOnly embedded/></DeFiProvider></AppShell>;
}
