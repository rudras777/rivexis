// Canonical Aave V3 normal-mode model. All monetary accounting uses bigint.
export const MODEL = 'aave-v3-normal-1';
export const WAD = 10n ** 18n;
export const USD = 10n ** 8n;
export function integer(value, name = 'integer') {
  if (typeof value !== 'string' || !/^\d{1,78}$/.test(value)) throw new Error(`Invalid ${name}`);
  if (BigInt(value) >= 2n ** 256n) throw new Error(`Overflow in ${name}`);
  return BigInt(value);
}
export function decimal(value, decimals = 8) {
  if (typeof value !== 'string' || !/^\d{1,18}(\.\d{1,18})?$/.test(value)) throw new Error('Enter a non-negative decimal');
  const [whole, fraction = ''] = value.split('.');
  if (fraction.length > decimals) throw new Error(`Maximum ${decimals} decimal places`);
  return BigInt(whole) * 10n ** BigInt(decimals) + BigInt(fraction.padEnd(decimals, '0') || '0');
}
export function format(value, decimals = 8, places = 2) {
  const n = BigInt(value), unit = 10n ** BigInt(decimals);
  return `${n / unit}${places ? '.' + (n % unit).toString().padStart(decimals, '0').slice(0, places).padEnd(places, '0') : ''}`;
}
export function validateSnapshot(snapshot, now = Date.now()) {
  if (!snapshot || snapshot.model !== MODEL || snapshot.status !== 'READY') throw new Error('A validated, supported snapshot is required');
  if (!Number.isSafeInteger(snapshot.blockTimestamp) || now / 1000 - snapshot.blockTimestamp > 180 || snapshot.blockTimestamp > now / 1000 + 30) throw new Error('Snapshot is stale; refresh on-chain evidence');
  if (!Array.isArray(snapshot.positions) || snapshot.positions.length > 4) throw new Error('Unsupported position count');
  const ids = new Set();
  for (const p of snapshot.positions) {
    if (ids.has(p.id) || p.protocol !== 'Aave V3' || p.chainId !== 1 || p.eMode !== 0) throw new Error('Unsupported or duplicate position');
    ids.add(p.id);
    if (!Array.isArray(p.reserves) || p.reserves.length > 80) throw new Error('Invalid reserves');
    const assets = new Set();
    for (const r of p.reserves) {
      if (assets.has(r.asset) || !/^0x[\da-fA-F]{40}$/.test(r.asset)) throw new Error('Invalid token identity');
      assets.add(r.asset);
      if (!Number.isInteger(r.decimals) || r.decimals < 0 || r.decimals > 36) throw new Error('Invalid token decimals');
      for (const key of ['collateralRaw', 'debtRaw', 'walletRaw', 'priceRaw', 'ltBps', 'allowanceRaw']) integer(r[key], key);
      if (integer(r.priceRaw) === 0n || integer(r.ltBps) > 10000n || r.oracleState !== 'FRESH' || r.isolation) throw new Error('Unsupported reserve/oracle evidence');
    }
  }
  return snapshot;
}
export function metrics(position, shocks = {}, actions = []) {
  let collateral = 0n, debt = 0n, weighted = 0n;
  for (const r of position.reserves) {
    const shock = shocks[r.asset.toLowerCase()] ?? 0;
    if (!Number.isInteger(shock) || shock < -9500 || shock > 10000) throw new Error('Price shock must be between -95% and +100%');
    const price = integer(r.priceRaw) * BigInt(10000 + shock) / 10000n;
    let c = integer(r.collateralRaw), d = integer(r.debtRaw);
    for (const a of actions.filter(a => a.positionId === position.id && a.asset.toLowerCase() === r.asset.toLowerCase())) {
      const amount = integer(a.amountRaw);
      if (a.kind === 'repay') { if (amount > d) throw new Error('Repayment exceeds debt'); d -= amount; }
      else if (a.kind === 'supply') { if (!r.collateralEnabled || !r.supplyAllowed) throw new Error('Collateral supply unsupported'); c += amount; }
      else if (a.kind === 'withdraw') { if (amount > c) throw new Error('Withdrawal exceeds supplied balance'); c -= amount; }
      else if (a.kind === 'borrow') d += amount;
      else throw new Error('Unsupported action');
    }
    const unit = 10n ** BigInt(r.decimals), cv = c * price / unit, dv = (d * price + unit - 1n) / unit;
    if (r.collateralEnabled) { collateral += cv; weighted += cv * integer(r.ltBps); }
    debt += dv;
  }
  // Current Aave V3 Origin GenericLogic: ceil debt valuation; retain the weighted
  // numerator for HF, apply wadDiv half-up, then divide by 10000 (no averaged-LT loss).
  const adjusted = weighted / 10000n;
  const hf = debt === 0n ? null : (weighted * WAD + debt / 2n) / debt / 10000n;
  return {collateralRaw: collateral.toString(), debtRaw: debt.toString(), adjustedRaw: adjusted.toString(), healthFactorRaw: hf?.toString() ?? null, liquidatable: hf !== null && hf < WAD};
}
export function scenario(snapshot, shocks = {}, actions = [], now = Date.now()) {
  validateSnapshot(snapshot, now);
  const assets = new Set(snapshot.positions.flatMap(p=>p.reserves.map(r=>r.asset.toLowerCase())));
  if(!shocks || typeof shocks !== 'object' || Array.isArray(shocks) || Object.keys(shocks).some(k=>!assets.has(k)))throw new Error('Unknown scenario asset');
  for(const a of actions){
    const p=snapshot.positions.find(p=>p.id===a.positionId);
    if(!p?.reserves.some(r=>r.asset.toLowerCase()===a.asset.toLowerCase()))throw new Error('Unsupported action position or asset');
  }
  return snapshot.positions.map(p => ({positionId:p.id, ...metrics(p, shocks, actions)}));
}
export function frontier(snapshot, {budget, target = '1.50', gasReserve = '0', shocks = {}, objective = 'target'}, now = Date.now()) {
  validateSnapshot(snapshot, now);
  const capital = decimal(budget), fees = decimal(gasReserve), goal = decimal(target, 18);
  if (goal < WAD || goal > 10n * WAD || fees > capital) throw new Error('Invalid target or fee reserve');
  if (!['target','max-min'].includes(objective)) throw new Error('Unsupported objective');
  const spendable = capital - fees, choices = [];
  const eth = snapshot.positions.flatMap(p=>p.reserves).find(r=>r.asset.toLowerCase()==='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2');
  const feeWei = eth ? (fees * WAD + integer(eth.priceRaw)-1n) / integer(eth.priceRaw) : null;
  const gasConstraint = feeWei === null ? 'UNKNOWN_ETH_PRICE' : integer(snapshot.nativeBalanceRaw) < feeWei ? 'INSUFFICIENT_NATIVE_GAS_RESERVE' : 'ASSUMED_FEE_RESERVE_COVERED';
  for (const p of snapshot.positions) for (const r of p.reserves) {
    if (integer(r.walletRaw) === 0n) continue;
    if (integer(r.debtRaw) > 0n) choices.push({positionId:p.id, r, kind:'repay'});
    if (r.collateralEnabled && r.supplyAllowed) choices.push({positionId:p.id, r, kind:'supply'});
  }
  if (choices.length > 12) throw new Error('Beta search supports at most 12 eligible actions');
  let examined = 0; const candidates = [], seen = new Set();
  function assess(allocations) {
    examined++; const actions = [], balances = new Map(); let spent = 0n;
    for (const [c, allocation] of allocations) {
      let amount = allocation * 10n ** BigInt(c.r.decimals) / integer(c.r.priceRaw);
      const key = c.r.asset.toLowerCase(), available = integer(c.r.walletRaw) - (balances.get(key) ?? 0n);
      if (amount > available) amount = available;
      if (c.kind === 'repay' && amount > integer(c.r.debtRaw)) amount = integer(c.r.debtRaw);
      if (amount === 0n) continue;
      balances.set(key, (balances.get(key) ?? 0n) + amount);
      spent += amount * integer(c.r.priceRaw) / 10n ** BigInt(c.r.decimals);
      actions.push({positionId:c.positionId, asset:c.r.asset, symbol:c.r.symbol, kind:c.kind, amountRaw:amount.toString(), decimals:c.r.decimals, approvalRequired:integer(c.r.allowanceRaw)<amount});
    }
    if (!actions.length || spent + fees > capital || gasConstraint === 'INSUFFICIENT_NATIVE_GAS_RESERVE') return;
    const key = JSON.stringify(actions); if (seen.has(key)) return; seen.add(key);
    const outcomes = scenario(snapshot, shocks, actions, now);
    const minHf = outcomes.reduce((m,o) => o.healthFactorRaw === null ? m : m === null || BigInt(o.healthFactorRaw) < m ? BigInt(o.healthFactorRaw) : m, null);
    const meetsTarget = outcomes.every(o => o.healthFactorRaw === null || BigInt(o.healthFactorRaw) >= goal);
    const uncovered = outcomes.filter(o => o.healthFactorRaw !== null && BigInt(o.healthFactorRaw) < goal).length;
    candidates.push({actions,capitalRaw:spent.toString(),totalBudgetRaw:(spent+fees).toString(),feeReserveRaw:fees.toString(),outcomes,minHealthFactorRaw:minHf?.toString() ?? null,meetsTarget,uncovered,feasibility:'MODELED_ONLY',execution:'NOT_SIMULATED',gasConstraint});
  }
  for (const c of choices) for (let step=1;step<=20;step++) assess([[c,spendable*BigInt(step)/20n]]);
  for (let i=0;i<choices.length;i++) for (let j=i+1;j<choices.length;j++) for (let step=1;step<20;step++) assess([[choices[i],spendable*BigInt(step)/20n],[choices[j],spendable*BigInt(20-step)/20n]]);
  const base = scenario(snapshot, shocks, [], now);
  // A zero-cost baseline must win a least-capital objective when the current
  // position already meets the chosen scenario target. No transaction means no gas.
  if(base.every(o=>o.healthFactorRaw===null||BigInt(o.healthFactorRaw)>=goal)){
    const minimum=base.reduce((m,o)=>o.healthFactorRaw===null?m:m===null||BigInt(o.healthFactorRaw)<m?BigInt(o.healthFactorRaw):m,null);
    candidates.push({actions:[],capitalRaw:'0',totalBudgetRaw:'0',feeReserveRaw:'0',outcomes:base,minHealthFactorRaw:minimum?.toString()??null,meetsTarget:true,uncovered:0,feasibility:'MODEL_BASELINE',execution:'NO_TRANSACTION',gasConstraint:'NOT_APPLICABLE'});
  }
  const value = c => c.minHealthFactorRaw === null ? 2n**255n : BigInt(c.minHealthFactorRaw);
  candidates.sort((a,b) => {
    if (objective === 'target' && a.meetsTarget !== b.meetsTarget) return a.meetsTarget ? -1 : 1;
    if (objective === 'target' && a.meetsTarget && b.meetsTarget) return BigInt(a.totalBudgetRaw)<BigInt(b.totalBudgetRaw)?-1:BigInt(a.totalBudgetRaw)>BigInt(b.totalBudgetRaw)?1:0;
    return value(a)>value(b)?-1:value(a)<value(b)?1:BigInt(a.totalBudgetRaw)<BigInt(b.totalBudgetRaw)?-1:1;
  });
  const representative = [];
  for(const type of ['repay','supply','combined']){
    const candidate=candidates.find(c=>type==='combined'?c.actions.length>1:c.actions.length===1&&c.actions[0].kind===type);
    if(candidate)representative.push(candidate);
  }
  const alternatives=[...new Set([...candidates.slice(0,5),...representative])].slice(0,8);
  return {model:MODEL,optimizer:'bounded-frontier-2',objective,budgetRaw:capital.toString(),targetRaw:goal.toString(),feeReserveRaw:fees.toString(),gasConstraint,baseline:base,examined,meetsTarget:candidates.some(c=>c.meetsTarget),alternatives,method:'Bounded enumeration: zero-cost current-state baseline; 5% budget increments; at most two actions per alternative; wallet balances shared by token. Leading ranked options plus repayment/supply/combination representatives. No swaps, bridging or global-optimum claim.',warnings:['Capital is valued at snapshot oracle prices; stress changes modeled position valuations only.','Fee reserve is a user assumption, not a gas estimate. Approvals may require additional fees.',gasConstraint==='INSUFFICIENT_NATIVE_GAS_RESERVE'?'Available native ETH cannot cover the assumed fee reserve; transaction alternatives withheld.':gasConstraint==='UNKNOWN_ETH_PRICE'?'Native gas affordability is unknown because a validated ETH price is absent.':'Observed ETH covers only the user-assumed fee reserve, not a guaranteed execution cost.','Every transaction alternative requires a fresh GasGuard preview; protocol caps, liquidity and execution may prevent the action.']};
}
