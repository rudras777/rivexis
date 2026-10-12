# Launch market source audit — 12 October 2026

The market display uses Ethereum mainnet public state from the fixed existing `https://ethereum.publicnode.com` endpoint. It sends no wallet addresses, authentication cookies, keys, signatures or transactions. PublicNode receives the browser's IP address and network metadata. The display is informational; these reference quotes do not replace Aave/Morpho position-specific protocol oracles in financial calculations.

## Primary references checked

- [Chainlink ETH/USD Ethereum standard feed](https://data.chain.link/feeds/ethereum/mainnet/eth-usd): standard proxy `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`.
- [Chainlink BTC/USD Ethereum standard feed](https://data.chain.link/feeds/ethereum/mainnet/btc-usd): standard proxy `0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c`.
- [Chainlink AggregatorV3 API](https://docs.chain.link/data-feeds/api-reference): decimals, signed answer, round IDs, startedAt and updatedAt. The adapter verifies both feeds return eight decimals at the observed block, rejects invalid/incomplete/nonpositive/future rounds, and retains integer answers before display conversion. The one-hour freshness limit is an application display policy, not a promise about feed heartbeat, trading timeliness or liquidation safety.
- [Ethereum execution API eth_feeHistory](https://ethereum.github.io/execution-apis/api/methods/eth_feeHistory/): the extra final base-fee entry concerns the next block and is excluded from measured history. Each actual fee sample is checked against an actual header with timestamp, hash and parent chain.
- [PublicNode official service](https://www.publicnode.com/?network=Mainnet): Ethereum public RPC is offered publicly; archive access is separately advertised. No account, paid archive plan or subscription was created. WebSocket transport is not required by this adapter.

Search indexing returned the official feed pages and abbreviated standard proxy addresses. Direct document fetches for some Chainlink pages were blocked; that limitation is not described as successful full-document retrieval. Runtime probes validated eight-decimal callable oracle interfaces at the fixed standard addresses.

## Rights and operating rationale

No exchange REST dataset is redistributed. In particular, Coinbase market data is excluded because the parent audit identified terms restricting third-party redistribution/display. This implementation reads public on-chain contract answers and canonical Ethereum headers through a publicly offered RPC. That is an engineering source choice, not legal certification of unrestricted sublicensing, a provider SLA or unlimited capacity. Source attribution remains visible. Provider availability and applicable service terms remain an operational dependency for public launch.

## Real probe evidence

`outputs/LAUNCH_MARKET_PROVIDER_PROBE.json` outside the checkout contains the complete actual Node-fetch observation. At Ethereum block **26176443**, hash **0xcbaaa6b1442993ea307d7a148f5bc14e8cbadfdbfa2be52b0470a59361116667**, observed block timestamp **1791808691**:

- ETH/USD raw answer `252109860445` / 1e8 = **2521.09860445**; oracle updatedAt **1791808667**, age **24 seconds**.
- BTC/USD raw answer `8268242161590` / 1e8 = **82682.4216159**; oracle updatedAt **1791808667**, age **24 seconds**.
- Four actual canonical fee headers returned, with real block times. Final pinned block hash and chain ID were rechecked.
- Sparse historical calls were incomplete: the final probe returned two of six historical observations for each symbol; other probes returned zero. Historical provider errors are retained and gaps are not fabricated, filled or called 24-hour coverage. Browser-origin CORS/production rendering is a separate release gate handled by the parent.
- `outputs/LAUNCH_MARKET_RECENT_ROUNDS_PROBE.json` marks **archiveFailureInjected: true**: only archive requests were deliberately rejected to test fallback. All current observations and six previous rounds for each feed came from actual PublicNode `getRoundData` calls at the current canonical hash. ETH round IDs **129127208515966895851–129127208515966895856**, actual updatedAt **1791793427–1791807923**, were returned. This verifies real fallback reads, not actual provider outage or 24-hour history coverage.
- A Python urllib provider probe received HTTP 403; the actual native Node-fetch adapter probe succeeded. No alternate paid provider or credentials were introduced.

## Bounds and validation

All method names, feed addresses and endpoint are fixed. Sequential batches contain at most four calls; response streaming is capped at 256 KiB; the complete observation times out after 25 seconds and propagates caller abort. Latest observations require Ethereum chain 1, a block no older than three minutes, EIP-1898 canonical hash-pinned oracle reads, and final chain/hash consistency. Four fee blocks are checked for actual header fee equality, parent linkage and chronological ordering. Historical reads request six sparse 1200-block intervals (approximately four hours apart), not synthetic hourly candles; actual block timestamps define the available span. If all archive quotes are unavailable, the adapter requests at most six previous rounds per feed at the current pinned hash, with actual oracle update times and explicit phase-boundary/gap errors. These are recent oracle observations, not hourly candles or guaranteed 24-hour coverage. Returned `history.mode` distinguishes the two sources; charts must plot `updatedAt` for recent oracle rounds.

The UI must prevent overlapping reads, poll only while visible, apply bounded retry/backoff, age observations against wall-clock time and preserve the last observation as stale when reconnecting. No extrapolated price, fabricated change percentage or fake success is authorized.

`node --test apps/web/lib/market-feed.test.mjs`: **21 scenarios passed**. Cases cover valid current/historical data, wrong chain, stale/future blocks, stale quotes, negative/zero quotes, incomplete/future rounds, decimal mismatch, archive gaps, reorg, malformed fee ranges, header mismatch, abort/offline, rate limiting/oversize, malformed batch identity, repeated samples/dedup/conflicts, invalid headers, recent-round genuine timestamps, recent-round conflicts/reverts, and phase boundaries. These deterministic tests are not live-provider uptime certification.

## Browser functional scenarios and correction

`npm --workspace @rivexis/web run test:e2e -- launch-market.spec.ts --workers=1`: **17/17 Chromium UI scenarios passed in 36.3 seconds** against the final local Next build. Browser RPC responses were mocked at the network boundary; these are real rendered UI tests with deterministic financial fixtures, not claims of live-provider coverage. Evidence is retained outside the checkout in `outputs/launch-market-browser-release-results.json` and `outputs/launch-market-browser-release-artifacts`.

Cases cover valid quote/fee charts and accessible tables, stale/negative/future quotes, wrong chain, offline and HTTP 429, disconnection retaining evidence and recovery, final reorg rejection, empty fee data, archive fallback with disclosure, missing-interval line breaks, repeated/manual refresh throttling and block advancement, hidden-tab pause/resume, authentication denial without feed requests, independent GasGuard network context without snapshot or transaction requests, and mobile controls without horizontal overflow.

The initial run passed 16/17: GasGuard network observations were hidden until a lending snapshot was selected. The parent corrected this functional issue by moving network context outside the snapshot-dependent rendering gate. A temporary test revision selecting a labeled sample passed, but that was superseded by the final regression requiring network charts **before selecting any sample or position**, with zero automatic snapshot calls and zero transaction calls. The final complete rerun passed all 17. Initial failure evidence remains in `outputs/launch-market-browser-initial-results.json`; it was not silently overwritten as a clean initial pass. The Playwright-owned server stopped after each completed run; no port 3000 listener remained.
