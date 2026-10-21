export interface MarketBlock { number: number; hash: string; parentHash: string; timestamp: number; baseFeeWei: string }
export interface OracleQuote { symbol: "ETH" | "BTC"; feed: string; decimals: number; answerRaw: string; priceUsd: number; updatedAt: number; ageSeconds: number; status: "FRESH" | "STALE"; roundId: string; blockNumber: number; blockHash: string; blockTimestamp: number }
export interface FeeSample { blockNumber: number; blockHash: string; timestamp: number; baseFeeWei: string }
export interface MarketSnapshot { source: string; rpc: string; chainId: 1; observedAt: number; block: MarketBlock; quotes: { ETH: OracleQuote | null; BTC: OracleQuote | null }; quoteErrors: { ETH?: string; BTC?: string }; fees: FeeSample[]; feeError?: string; history: { ETH: OracleQuote[]; BTC: OracleQuote[]; errors: string[]; requested: boolean; mode: "sampled-blocks" | "recent-oracle-rounds" | "mixed-observations" } }
export const MARKET_RPC: string;
export const MARKET_FEEDS: Readonly<{ ETH: string; BTC: string }>;
export function validateMarketBlock(value: unknown, expected?: number): MarketBlock;
export function decodeOracleQuote(value: unknown, symbol: "ETH" | "BTC", block: MarketBlock): OracleQuote;
export function createMarketReader(dependencies?: { fetchImpl?: typeof fetch; now?: () => number }): (options?: { signal?: AbortSignal; history?: boolean }) => Promise<MarketSnapshot>;
export function readMarket(options?: { signal?: AbortSignal; history?: boolean }): Promise<MarketSnapshot>;
export function mergeMarketSamples(previous: FeeSample[], incoming: FeeSample[], limit?: number): FeeSample[];
