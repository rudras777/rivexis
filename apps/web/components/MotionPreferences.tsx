"use client";
import {useEffect,useState} from 'react';
import {APPEARANCE_CACHE} from './AccountPreferences';
export function MotionPreferences(){
 const [reduced,setReduced]=useState(false);
 useEffect(()=>{const update=()=>setReduced(document.documentElement.dataset.motion==='reduce');update();window.addEventListener('rivexis-appearance-change',update);return()=>window.removeEventListener('rivexis-appearance-change',update)},[]);
 function change(){const motion=reduced?'system':'reduce';try{const previous=JSON.parse(localStorage.getItem(APPEARANCE_CACHE)||'{}');const allowed:Record<string,unknown>={};for(const key of ['theme','motion','contrast','density','textSize'])if(previous&&typeof previous==='object'&&Object.hasOwn(previous,key))allowed[key]=previous[key];localStorage.setItem(APPEARANCE_CACHE,JSON.stringify({...allowed,motion}))}catch{}window.dispatchEvent(new CustomEvent('rivexis-public-motion',{detail:motion}));}
 return <details className="publicMotionPreferences"><summary>Motion preferences</summary><p>Control decorative motion on this device. Your device’s reduced-motion setting is always respected. Account preferences are also available in Settings → Appearance.</p><button className="textButton" type="button" aria-pressed={reduced} onClick={change}>{reduced?'Resume background motion':'Pause background motion'}</button></details>;
}
