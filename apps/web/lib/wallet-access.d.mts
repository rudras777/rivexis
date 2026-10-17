export const WALLET_REQUEST_TIMEOUT_MS: 35000;
export class WalletAccessError extends Error { code: string; constructor(code: string, message: string); }
export interface WalletAccessProvider { request(input: { method: string }): Promise<unknown>; }
export function requestWalletAccess(provider: WalletAccessProvider, options?: { signal?: AbortSignal; isCurrent?: () => boolean; timeoutMs?: number }): Promise<string>;
