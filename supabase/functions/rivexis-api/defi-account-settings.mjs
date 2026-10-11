import {storedPreferences,validateAccountUpdate} from './account-preferences.mjs';
import {readRequestText} from './defi-http.mjs';
export function accountView(user){return {profile:{displayName:typeof user.user_metadata?.display_name==='string'?user.user_metadata.display_name.slice(0,60):'',email:user.email??'',emailVerified:Boolean(user.email_confirmed_at),createdAt:user.created_at??null,lastSignInAt:user.last_sign_in_at??null},preferences:storedPreferences(user.user_metadata?.rivexis_preferences)};}
// Services are injected so actor scoping, CSRF, validation and failures are tested.
export async function accountSettings(req,auth,admin,routePath){
 const reply=(body,status=200)=>({body,status});
 if(!auth?.user?.id)return reply({detail:'Authentication required'},401);
 if(!auth.user.email_confirmed_at)return reply({detail:'Email verification required'},403);
 const path=routePath??new URL(req.url).pathname,method=req.method.toUpperCase();
 if(new URL(req.url).search)return reply({detail:'Account operations do not accept an actor selector'},422);
 if(method!=='GET'&&req.headers.get('x-rivexis-csrf')!==auth.session?.csrf)return reply({detail:'CSRF validation failed'},403);
 if(path==='/api/v1/account/settings'&&method==='GET')return reply(accountView(auth.user));
 if(path==='/api/v1/account/settings'&&method==='PATCH'){
  let input;try{input=validateAccountUpdate(JSON.parse(await readRequestText(req,8192)))}catch{return reply({detail:'Check your display name, preference values, budget and saved addresses'},422)}
  const metadata={...(auth.user.user_metadata??{}),display_name:input.displayName,rivexis_preferences:input.preferences};
  const {data,error}=await admin.auth.admin.updateUserById(auth.user.id,{user_metadata:metadata});
  return error||!data?.user||data.user.id!==auth.user.id?reply({detail:'Account settings could not be saved'},503):reply(accountView(data.user));
 }
 if(path==='/api/v1/account/sessions/others'&&method==='POST'){
  let input;try{input=JSON.parse(await readRequestText(req,256))}catch{return reply({detail:'Invalid session request'},422)}
  if(!input||Object.keys(input).length!==1||input.confirm!==true)return reply({detail:'Explicit session confirmation required'},422);
  const {error}=await admin.auth.admin.signOut(auth.session.access_token,'others');
  return error?reply({detail:'Other sessions could not be ended'},503):reply({status:'OTHER_REFRESH_SESSIONS_ENDED',accessTokensMayRemainValidUntilExpiry:true});
 }
 if(path==='/api/v1/account/export'&&method==='GET'){
  const result=await admin.from('rivexis_defi_reports').select('id,created_at,receipt').eq('owner_id',auth.user.id).order('created_at',{ascending:false}).limit(20);
  if(result.error)return reply({detail:'Account export is temporarily unavailable'},503);
  return reply({brand:'RIVEXIS',classification:'OWNER_PROFILE_PREFERENCES_AND_SAVED_RISK_RECEIPTS',...accountView(auth.user),reports:result.data,exportedAt:new Date().toISOString(),scope:'Profile, preferences and up to 20 owner-saved risk receipts. Shared organization records and authentication credentials are excluded.'});
 }
 return reply({detail:'Unsupported account operation'},405);
}
