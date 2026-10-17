import { getAddress, isAddress } from 'viem';

export const WALLET_REQUEST_TIMEOUT_MS = 35_000;
export class WalletAccessError extends Error {
  constructor(code, message) { super(message); this.name = 'WalletAccessError'; this.code = code; }
}
const cancelled = () => new WalletAccessError('CANCELLED', 'RIVEXIS stopped waiting. A request may still be pending in your wallet; review it before trying again.');

/** EIP-1193 requests cannot be withdrawn from a wallet. Stop waiting locally and ignore late results. */
export async function requestWalletAccess(provider, { signal, isCurrent = () => true, timeoutMs = WALLET_REQUEST_TIMEOUT_MS } = {}) {
  if (!provider || typeof provider.request !== 'function') throw new TypeError('A wallet provider is required');
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > WALLET_REQUEST_TIMEOUT_MS) throw new RangeError('Invalid wallet request deadline');
  if (signal?.aborted || !isCurrent()) throw cancelled();
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  let rejectAbort;
  const aborted = new Promise((_, reject) => { rejectAbort = reject; });
  // A caller can invalidate synchronously before the first race is attached.
  void aborted.catch(() => {});
  const onAbort = () => rejectAbort(timedOut
    ? new WalletAccessError('TIMEOUT', 'Wallet connection timed out. A request may still be pending in your wallet; review it before trying again. No signature or transaction was requested.')
    : cancelled());
  controller.signal.addEventListener('abort', onAbort, { once: true });
  const check = () => { if (controller.signal.aborted || !isCurrent()) throw cancelled(); };
  const request = async (method) => {
    check();
    const value = await Promise.race([Promise.resolve().then(() => { check(); return provider.request({ method }); }), aborted]);
    check();
    return value;
  };
  try {
    if (await request('eth_chainId') !== '0x1') throw new WalletAccessError('UNSUPPORTED_NETWORK', 'Choose Ethereum mainnet in your wallet before connecting. RIVEXIS will not switch networks automatically.');
    const accounts = await request('eth_requestAccounts');
    if (!Array.isArray(accounts) || typeof accounts[0] !== 'string' || !isAddress(accounts[0], { strict: true }) || /^0x0{40}$/i.test(accounts[0])) throw new WalletAccessError('INVALID_ACCOUNT', 'Wallet did not expose a valid Ethereum account.');
    if (await request('eth_chainId') !== '0x1') throw new WalletAccessError('NETWORK_CHANGED', 'Network changed during connection. Choose Ethereum mainnet and retry.');
    return getAddress(accounts[0]);
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', abort);
    controller.signal.removeEventListener('abort', onAbort);
  }
}
