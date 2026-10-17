import test from 'node:test';
import assert from 'node:assert/strict';
import { requestWalletAccess, WalletAccessError } from './wallet-access.mjs';

const address = '0x' + '1'.repeat(40);
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
const waitFor = async condition => { for (let i = 0; i < 100 && !condition(); i++) await Promise.resolve(); assert.ok(condition(), 'Expected provider stage was reached'); };
function fixture({ stage = 0, wrongChain = false, accounts = [address], failure } = {}) {
  const gate = deferred(), calls = [];
  return { calls, gate, provider: { request: async ({ method }) => {
    calls.push(method);
    if (calls.length === stage) return gate.promise;
    if (failure && method === 'eth_requestAccounts') throw failure;
    return method === 'eth_requestAccounts' ? accounts : wrongChain ? '0x89' : '0x1';
  } } };
}

test('wallet access succeeds using only chain/address/chain, never signing or sending', async () => {
  const f = fixture(); assert.equal(await requestWalletAccess(f.provider), address);
  assert.deepEqual(f.calls, ['eth_chainId', 'eth_requestAccounts', 'eth_chainId']);
});
test('unsupported network rejects before requesting account permission', async () => {
  const f = fixture({ wrongChain: true }); await assert.rejects(requestWalletAccess(f.provider), e => e.code === 'UNSUPPORTED_NETWORK');
  assert.deepEqual(f.calls, ['eth_chainId']);
});
test('network change during permission request withholds the address', async () => {
  let calls = 0; await assert.rejects(requestWalletAccess({ request: async ({ method }) => ++calls === 3 ? '0x89' : method === 'eth_requestAccounts' ? [address] : '0x1' }), e => e.code === 'NETWORK_CHANGED');
});
test('empty, malformed, zero and bad-checksum accounts reject before a final chain read', async () => {
  for (const accounts of [[], null, ['private key'], ['0x' + '0'.repeat(40)], ['0x52908400098527886E0F7030069857D2E4169Ee7']]) {
    const f = fixture({ accounts }); await assert.rejects(requestWalletAccess(f.provider), e => e.code === 'INVALID_ACCOUNT'); assert.equal(f.calls.length, 2);
  }
});
for (const code of [4001, -32002]) test(`provider rejection ${code} is preserved without retry`, async () => {
  const f = fixture({ failure: { code } }); await assert.rejects(requestWalletAccess(f.provider), e => e.code === code); assert.equal(f.calls.length, 2);
});
test('pre-cancelled or unauthorized access makes no provider request', async () => {
  const f = fixture(), controller = new AbortController(); controller.abort();
  await assert.rejects(requestWalletAccess(f.provider, { signal: controller.signal }), e => e.code === 'CANCELLED');
  await assert.rejects(requestWalletAccess(f.provider, { isCurrent: () => false }), e => e.code === 'CANCELLED'); assert.equal(f.calls.length, 0);
});
for (const stage of [1, 2, 3]) test(`cancellation during provider stage ${stage} ignores late resolution and makes no later request`, async () => {
  const f = fixture({ stage }), controller = new AbortController();
  const result = requestWalletAccess(f.provider, { signal: controller.signal });
  await waitFor(() => f.calls.length === stage); controller.abort();
  await assert.rejects(result, e => e.code === 'CANCELLED'); f.gate.resolve(stage === 2 ? [address] : '0x1');
  await Promise.resolve(); await Promise.resolve(); assert.equal(f.calls.length, stage);
});
for (const stage of [1, 2, 3]) test(`stalled provider stage ${stage} times out without inventing a connection`, async () => {
  const f = fixture({ stage });
  await assert.rejects(requestWalletAccess(f.provider, { timeoutMs: 20 }), e => e instanceof WalletAccessError && e.code === 'TIMEOUT' && /may still be pending/.test(e.message));
  f.gate.resolve(stage === 2 ? [address] : '0x1'); await Promise.resolve(); assert.equal(f.calls.length, stage);
});
test('the total deadline spans chain and account stages rather than resetting per request', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const first = deferred(), calls = [];
  const result = requestWalletAccess({ request: ({ method }) => { calls.push(method); return calls.length === 1 ? first.promise : new Promise(() => {}); } });
  await waitFor(() => calls.length === 1); t.mock.timers.tick(20_000); first.resolve('0x1');
  await waitFor(() => calls.length === 2); t.mock.timers.tick(15_001);
  await assert.rejects(result, e => e.code === 'TIMEOUT'); assert.equal(calls.length, 2);
});
test('authority loss between stages prevents the account-permission request', async () => {
  let current = true, calls = 0;
  await assert.rejects(requestWalletAccess({ request: async () => { calls++; current = false; return '0x1'; } }, { isCurrent: () => current }), e => e.code === 'CANCELLED');
  assert.equal(calls, 1);
});
test('an explicit new attempt can succeed after a timeout without accepting the old result', async () => {
  const old = fixture({ stage: 2 }); await assert.rejects(requestWalletAccess(old.provider, { timeoutMs: 20 }), e => e.code === 'TIMEOUT');
  const fresh = fixture(); assert.equal(await requestWalletAccess(fresh.provider), address); old.gate.resolve(['0x' + '2'.repeat(40)]);
  await Promise.resolve(); assert.equal(old.calls.length, 2); assert.equal(fresh.calls.length, 3);
});
test('successful access clears its timer so later time cannot invalidate success', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] }); const f = fixture(); assert.equal(await requestWalletAccess(f.provider), address); t.mock.timers.tick(40_000); assert.equal(f.calls.length, 3);
});
test('invalid deadline or missing provider rejects before requesting permission', async () => {
  const f = fixture(); for (const timeoutMs of [0, -1, 35001, NaN]) await assert.rejects(requestWalletAccess(f.provider, { timeoutMs }), RangeError);
  await assert.rejects(requestWalletAccess(null), TypeError); assert.equal(f.calls.length, 0);
});
