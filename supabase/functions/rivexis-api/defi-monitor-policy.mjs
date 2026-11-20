import {decimal, integer, WAD} from './defi-model.mjs';
import {validateSnapshot, metrics} from './defi-unified-model.mjs';
import {validWallet} from './defi-http.mjs';
import {COVERAGE} from './defi-portfolio-rpc.mjs';

// Configuration never accepts an owner, recipient, URL, protocol deployment or price.
export function monitorInput(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(k => !['wallet','coverage','threshold','recovery','enabled','emailOptIn'].includes(k))) throw new Error('Unsupported monitoring settings');
  if (!validWallet(input.wallet) || !COVERAGE.includes(input.coverage)) throw new Error('Select a supported Ethereum wallet and coverage');
  if (typeof input.enabled !== 'boolean' || typeof input.emailOptIn !== 'boolean') throw new Error('Explicit monitoring and email preferences required');
  const threshold = decimal(input.threshold,18), recovery = decimal(input.recovery,18);
  if (threshold < WAD || threshold > 3n*WAD || recovery < threshold+WAD/20n || recovery > 4n*WAD) throw new Error('Use a threshold from 1 to 3 and recovery at least 0.05 higher, up to 4');
  return {wallet:input.wallet.toLowerCase(),coverage:input.coverage,threshold_raw:threshold.toString(),recovery_raw:recovery.toString(),enabled:input.enabled,email_opt_in:input.emailOptIn};
}

// Recompute from validated protocol positions; ignore display quotes and the
// caller's aggregate observedHealthFactorRaw. No hypothetical shocks are applied.
export function evaluateMonitor(rule, snapshot, now=Date.now()) {
  if (!rule || !validWallet(rule.wallet) || !COVERAGE.includes(rule.coverage)) throw new Error('Invalid rule identity');
  if (snapshot?.sample || snapshot?.restoredReport || snapshot?.chainId!==1 || snapshot?.wallet?.toLowerCase()!==rule.wallet.toLowerCase() || (snapshot.coverage??'aave')!==rule.coverage || !/^\d{1,20}$/.test(snapshot.blockNumber) || !/^0x[\da-f]{64}$/i.test(snapshot.blockHash)) throw new Error('Monitoring requires matching live protocol evidence');
  validateSnapshot(snapshot,now);
  const threshold=integer(rule.threshold_raw),recovery=integer(rule.recovery_raw);
  if(threshold<WAD||threshold>3n*WAD||recovery<threshold+WAD/20n||recovery>4n*WAD)throw new Error('Invalid thresholds');
  const health=snapshot.positions.map(p=>metrics(p).healthFactorRaw).filter(x=>x!==null).map(BigInt).reduce((low,n)=>low===null||n<low?n:low,null);
  // Hysteresis preserves a breach through the band; missing evidence must never
  // clear it. A debt-free position has no finite health factor.
  const condition=health===null||health>=recovery?'CLEAR':health<=threshold?'BREACH':rule.condition==='BREACH'?'BREACH':'CLEAR';
  return {condition,health_raw:health?.toString()??null,block_number:snapshot.blockNumber,block_hash:snapshot.blockHash.toLowerCase(),block_timestamp:snapshot.blockTimestamp,evaluated_at:new Date(now).toISOString(),source:'Ethereum / validated protocol oracles',coverage:rule.coverage};
}

export function deliveryOutcome(status,body) {
  // A 2xx without a receipt, a transport timeout and a duplicate response with
  // no receipt all have unknown outcomes. They must not cause a blind resend.
  if(status>=200&&status<300&&typeof body?.messageId==='string'&&body.messageId.length>0&&body.messageId.length<=300)return {state:'ACCEPTED',message_id:body.messageId};
  if(status===429)return {state:'RETRY',error_code:'RATE_LIMITED'};
  if(status>=400&&status<500&&status!==408&&!['duplicate_parameter','duplicateparameter'].includes(String(body?.code??'').toLowerCase()))return {state:'FAILED',error_code:'PROVIDER_REJECTED'};
  return {state:'UNKNOWN',error_code:'ACCEPTANCE_UNCONFIRMED'};
}
