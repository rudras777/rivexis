"use client";
import {createContext,useContext,useEffect,type ReactNode} from "react";
import {usePathname} from "next/navigation";
import {useQuery} from "@tanstack/react-query";
import {api} from "@/lib/api";
import {DEFAULT_PREFERENCES,storedPreferences,type Preferences} from "../../../supabase/functions/rivexis-api/account-preferences.mjs";
export type AccountSettings={profile:{displayName:string;email:string;emailVerified:boolean;createdAt:string|null;lastSignInAt:string|null};preferences:Preferences};
export const APPEARANCE_CACHE="rivexis_appearance";
export function applyAppearance(p:Preferences){
 const root=document.documentElement;root.dataset.theme=p.theme==='system'?(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark'):p.theme;root.dataset.motion=p.motion;root.dataset.contrast=p.contrast;root.dataset.density=p.density;root.dataset.textSize=p.textSize;
 window.dispatchEvent(new Event('rivexis-appearance-change'));
}
const Context=createContext<{preferences:Preferences;account:AccountSettings|null}>({preferences:DEFAULT_PREFERENCES,account:null});
export function AccountPreferencesProvider({children}:{children:ReactNode}){
 const path=usePathname();const q=useQuery({queryKey:['account-settings'],queryFn:({signal})=>api<AccountSettings>('/api/v1/account/settings',{signal}),enabled:path.startsWith('/workspace'),retry:false});
 const account=q.data??null,preferences=account?.preferences??DEFAULT_PREFERENCES;
 useEffect(()=>{
  let current=preferences;
  if(!account){try{const cached=JSON.parse(localStorage.getItem(APPEARANCE_CACHE)||'null');current=storedPreferences({theme:cached?.theme??(localStorage.getItem('rivexis_theme')==='light'?'light':'dark'),motion:cached?.motion??'system',contrast:cached?.contrast??'standard',density:cached?.density??'comfortable',textSize:cached?.textSize??'standard'});}catch{}}
  const update=()=>applyAppearance(current);update();const media=matchMedia('(prefers-color-scheme:light)');media.addEventListener('change',update);
  if(account){const {theme,motion,contrast,density,textSize}=preferences;try{localStorage.setItem(APPEARANCE_CACHE,JSON.stringify({theme,motion,contrast,density,textSize}));localStorage.setItem('rivexis_theme',document.documentElement.dataset.theme||'dark')}catch{}}
  const motion=(event:Event)=>{const value=(event as CustomEvent).detail;if(value!=='reduce'&&value!=='system')return;current={...current,motion:value};update()};window.addEventListener('rivexis-public-motion',motion);return()=>{media.removeEventListener('change',update);window.removeEventListener('rivexis-public-motion',motion)};
 },[account,preferences]);
 return <Context.Provider value={{preferences,account}}>{children}</Context.Provider>;
}
export function useAccountPreferences(){return useContext(Context)}
