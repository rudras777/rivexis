"use client";

import {createContext,useContext} from "react";

export type WorkspaceSummary={
  id:string;
  name:string;
  role:string;
  organization_id?:string|null;
  access_role:string;
};

type WorkspaceContextValue={
  workspaceId:string;
  workspace:WorkspaceSummary;
  workspaces:WorkspaceSummary[];
  switchWorkspace:(workspaceId:string)=>void;
};

const WorkspaceContext=createContext<WorkspaceContextValue|null>(null);

export function WorkspaceContextProvider({value,children}:{value:WorkspaceContextValue;children:React.ReactNode}){
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(){
  const value=useContext(WorkspaceContext);
  if(!value)throw new Error("Workspace context is unavailable outside the authenticated workspace shell");
  return value;
}

export function workspaceQueryKey(workspaceId:string,scope:string,...parts:Array<string|number|boolean>){
  return ["workspace",workspaceId,scope,...parts] as const;
}
