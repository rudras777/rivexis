import {api,ApiError} from './api';
import {DEFAULT_PREFERENCES,validatePreferences,type Preferences} from '../../../supabase/functions/rivexis-api/account-preferences.mjs';

export type AccountSettings={profile:{displayName:string;email:string;emailVerified:boolean;createdAt:string|null;lastSignInAt:string|null};preferences:Preferences};
const record=(value:unknown):value is Record<string,unknown>=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const invalid=()=>new ApiError(502,'Account settings could not be verified. Retry when the service is available.');

// A TypeScript generic does not validate an HTTP response. Do not publish an
// incomplete account or silently substitute financial defaults into the cache.
export function decodeAccountSettings(value:unknown):AccountSettings{
 if(!record(value)||!record(value.profile)||!record(value.preferences))throw invalid();
 const p=value.profile;
 if(typeof p.displayName!=='string'||p.displayName.length>60||typeof p.email!=='string'||p.email.length>320||typeof p.emailVerified!=='boolean')throw invalid();
 for(const field of ['createdAt','lastSignInAt'])if(p[field]!=null&&(typeof p[field]!=='string'||!Number.isFinite(Date.parse(p[field] as string))))throw invalid();
 if(Object.keys(DEFAULT_PREFERENCES).some(key=>!Object.hasOwn(value.preferences as object,key)))throw invalid();
 let preferences:Preferences;
 try{preferences=validatePreferences(value.preferences)}catch{throw invalid()}
 return {profile:{displayName:p.displayName,email:p.email,emailVerified:p.emailVerified,createdAt:p.createdAt as string|null??null,lastSignInAt:p.lastSignInAt as string|null??null},preferences};
}

export async function requestAccountSettings(init:RequestInit={}):Promise<AccountSettings>{
 return decodeAccountSettings(await api<unknown>('/api/v1/account/settings',init));
}
