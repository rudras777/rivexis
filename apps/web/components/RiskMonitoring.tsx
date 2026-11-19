"use client";
import {useEffect,useRef,useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {api} from '@/lib/api';
import {displayedDate,displayedHealth} from '@/lib/financial-display';
import {useAccountPreferences} from './AccountPreferences';

type Rule={wallet:string;coverage:string;threshold_raw:string;recovery_raw:string;enabled:boolean;email_opt_in:boolean;last_status:string;last_success_at:string|null;last_attempt_at:string|null;block_number:string|null;block_hash:string|null;condition:string;health_raw:string|null;next_evaluation_at:string};
type Event={id:string;kind:string;state:string;created_at:string;block_number:string;error_code:string|null};
type Records={runtime:{state:'INACTIVE'|'SCHEDULED';email:boolean;interval_minutes:30;last_cycle_at?:string|null};rule:Rule|null;events:Event[]};
function decode(value:unknown):Records{
 const v=value as Records;
 if(!v||!v.runtime||!['INACTIVE','SCHEDULED'].includes(v.runtime.state)||typeof v.runtime.email!=='boolean'||v.runtime.interval_minutes!==30||!Array.isArray(v.events)||v.events.length>20||v.rule===undefined)throw new Error('Monitoring response could not be verified');
 if(v.rule&&(!/^0x[\da-f]{40}$/.test(v.rule.wallet)||!['aave','morpho-wbtc','combined'].includes(v.rule.coverage)||!/^\d{19}$/.test(v.rule.threshold_raw)||!/^\d{19}$/.test(v.rule.recovery_raw)||typeof v.rule.enabled!=='boolean'||typeof v.rule.email_opt_in!=='boolean'||!['UNKNOWN','CLEAR','BREACH'].includes(v.rule.condition)||!['NEVER_EVALUATED','VERIFIED','UNAVAILABLE','INVALIDATED'].includes(v.rule.last_status)))throw new Error('Monitoring rule could not be verified');
 if(v.rule&&((v.rule.health_raw!==null&&!/^\d{1,78}$/.test(v.rule.health_raw))||[v.rule.last_success_at,v.rule.last_attempt_at].some(t=>t!==null&&!Number.isFinite(Date.parse(t)))||(v.rule.block_number!==null&&!/^\d{1,20}$/.test(v.rule.block_number))||(v.rule.block_hash!==null&&!/^0x[\da-f]{64}$/.test(v.rule.block_hash))))throw new Error('Monitoring evidence could not be verified');
 if(v.events.some(e=>!e||typeof e.id!=='string'||!['BREACH','RECOVERY'].includes(e.kind)||!['QUEUED','SENDING','ACCEPTED','DELIVERED','BOUNCED','FAILED','UNKNOWN','EXPIRED','CANCELLED','INVALIDATED'].includes(e.state)||!Number.isFinite(Date.parse(e.created_at))))throw new Error('Notification history could not be verified');
 return v;
}
export function RiskMonitoring(){
 const {account}=useAccountPreferences();
 return account?.profile.emailVerified?<MonitoringAccount key={account.profile.email}/>:null;
}
function MonitoringAccount(){
 const {account,preferences}=useAccountPreferences(),qc=useQueryClient(),key=['defi-monitor',account?.profile.email];
 const q=useQuery({queryKey:key,queryFn:async({signal})=>decode(await api('/api/v1/defi/monitor',{signal})),retry:false,staleTime:0});
 const [wallet,setWallet]=useState(''),[coverage,setCoverage]=useState('aave'),[threshold,setThreshold]=useState('1.20'),[recovery,setRecovery]=useState('1.30'),[enabled,setEnabled]=useState(false),[email,setEmail]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const loaded=useRef<Records|null>(null),alive=useRef(true),[clock,setClock]=useState(Date.now());
 useEffect(()=>{alive.current=true;const timer=setInterval(()=>setClock(Date.now()),30000);return()=>{alive.current=false;clearInterval(timer)}},[]);
 useEffect(()=>{if(!q.data||loaded.current===q.data)return;loaded.current=q.data;const r=q.data.rule;if(r){setWallet(r.wallet);setCoverage(r.coverage);setThreshold(rawDecimal(r.threshold_raw));setRecovery(rawDecimal(r.recovery_raw));setEnabled(r.enabled);setEmail(r.email_opt_in)}},[q.data]);
 async function save(){
  if(busy)return;setBusy(true);setError('');setNotice('');
  try{const result=decode(await api('/api/v1/defi/monitor',{method:'PATCH',body:JSON.stringify({wallet,coverage,threshold,recovery,enabled,emailOptIn:email}),signal:AbortSignal.timeout(15000)}));const saved=result.rule;if(!saved||saved.wallet!==wallet.toLowerCase()||saved.coverage!==coverage||saved.threshold_raw!==decimalRaw(threshold)||saved.recovery_raw!==decimalRaw(recovery)||saved.enabled!==enabled||saved.email_opt_in!==email)throw new Error('Unconfirmed save');if(alive.current){qc.setQueryData(key,result);setNotice('Monitoring preferences saved. Scheduled checks and notification delivery have separate availability.')}}
  catch{if(alive.current)setError('Save could not be confirmed. Reload monitoring records before retrying; no automatic retry was made.')}
  finally{if(alive.current)setBusy(false)}
 }
 const data=q.data,rule=data?.rule,cycleTime=Date.parse(data?.runtime.last_cycle_at??''),scheduled=!q.error&&data?.runtime.state==='SCHEDULED'&&Number.isFinite(cycleTime)&&clock-cycleTime<=900000&&cycleTime-clock<=30000,date=(v:string|null|undefined)=>v?displayedDate(v,preferences.timezone):'Never';
 return <section className="instrumentPanel riskMonitoring" aria-label="Scheduled risk monitoring"><div className="eyebrow">PROTOCOL EVIDENCE / NOTIFICATIONS</div><h2>Scheduled risk monitoring</h2>
 <p>One private Ethereum rule per account, checked about every 30 minutes by the server when activated. Aave V3 normal mode and the validated Morpho WBTC/USDC market retain separate liquidation domains.</p>
 <p className="marketFreshness" role="status">{q.isPending?'Reading monitoring availability…':q.error?'Monitoring records unavailable; coverage is unverified':scheduled?'Scheduled worker available': 'Scheduled monitoring inactive. No continuous protection is active.'}</p>
 <button className="ghost" type="button" disabled={q.isFetching||busy} onClick={()=>{setError('');void q.refetch()}}>Reload monitoring records</button>
 {data&&<><dl className="monitorEvidence"><dt>Server cycle</dt><dd>{date(data.runtime.last_cycle_at)}</dd><dt>Latest evaluation attempt</dt><dd>{date(rule?.last_attempt_at)}</dd><dt>Latest successful evaluation</dt><dd>{date(rule?.last_success_at)}{rule&&` · ${rule.last_status}`}</dd><dt>Email delivery</dt><dd>{data.runtime.email?'Available to explicitly opted-in rules':'Inactive — verification and recovery mail remain separate'}</dd></dl>
 {rule&&<p className="muted">Latest retained condition: {rule.condition}. Health: {rule.health_raw?displayedHealth(rule.health_raw,preferences.healthPrecision):'No finite health observation'}. {rule.block_number&&`Ethereum block ${rule.block_number}.`} This is the last recorded evaluation, not a current safety guarantee.</p>}
 {(scheduled||rule)&&<form onSubmit={e=>{e.preventDefault();void save()}}><fieldset disabled={busy}><legend>Private monitoring rule</legend><div className="settingsFields"><label className="field">Public Ethereum address<input value={wallet} onChange={e=>setWallet(e.target.value.trim())} maxLength={42} required spellCheck={false}/></label><label className="field">Validated coverage<select value={coverage} onChange={e=>setCoverage(e.target.value)}><option value="aave">Aave V3 · normal mode</option><option value="morpho-wbtc">Morpho · WBTC/USDC 86% LLTV</option><option value="combined">Aave + validated Morpho</option></select></label><label className="field">Alert at or below health factor<input value={threshold} onChange={e=>setThreshold(e.target.value)} inputMode="decimal" required/></label><label className="field">Recover at or above health factor<input value={recovery} onChange={e=>setRecovery(e.target.value)} inputMode="decimal" required/></label></div>
 <label className="settingCheck"><input type="checkbox" checked={enabled} disabled={!scheduled&&!enabled} onChange={e=>setEnabled(e.target.checked)}/>Enable scheduled evaluation for this address</label><label className="settingCheck"><input type="checkbox" checked={email} onChange={e=>setEmail(e.target.checked)}/>Email me threshold and recovery notifications at my verified account address</label><p className="muted">Email is optional and off by default. Missing or stale evidence cannot trigger a successful risk evaluation. Notifications contain no wallet balances. Checks can stop during outages, exhausted quotas or unvalidated protocol changes; review the last successful evaluation.</p><button className="button" type="submit" disabled={!!q.error||(!scheduled&&enabled)}>{busy?'Saving…':'Save monitoring preferences'}</button></fieldset></form>}
 {data.events.length>0&&<details><summary>Recent risk notifications</summary><div className="tableScroll"><table><thead><tr><th>Observation</th><th>Event</th><th>Delivery state</th></tr></thead><tbody>{data.events.map(e=><tr key={e.id}><td>{date(e.created_at)}<br/>Block {e.block_number}</td><td>{e.kind}</td><td>{e.state}</td></tr>)}</tbody></table></div><p className="muted">Accepted means the email provider returned a receipt. Delivered or bounced requires separate provider evidence. Unknown outcomes are held for reconciliation and are never blindly resent.</p></details>}</>}
 {error&&<p className="error" role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}<p className="muted">Thirty-minute checks can miss rapid price movements. No guaranteed warning, signing or automatic transaction is provided. The five bounded browser checks below work independently.</p>
 </section>;
}
function rawDecimal(raw:string){const value=BigInt(raw),fraction=(value%10n**18n).toString().padStart(18,'0').replace(/0+$/,'');return `${value/10n**18n}${fraction?'.'+fraction:''}`}
function decimalRaw(value:string){if(!/^\d{1,18}(\.\d{1,18})?$/.test(value))return null;const [whole,fraction='']=value.split('.');return (BigInt(whole)*10n**18n+BigInt(fraction.padEnd(18,'0'))).toString()}
