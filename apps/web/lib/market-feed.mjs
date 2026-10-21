// Public, read-only market observations. Never use these display quotes for position calculations.
export const MARKET_RPC = "https://ethereum.publicnode.com";
export const MARKET_FEEDS = Object.freeze({
  ETH: "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419",
  BTC: "0xf4030086522a5beea4988f8ca5b36dbc97bee88c",
});
const HASH = /^0x[0-9a-fA-F]{64}$/;
const HEX = /^0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)$/;
const quantity = (value) => {
  if (typeof value !== "string" || !HEX.test(value) || value.length > 66) throw new Error("Invalid RPC integer");
  return BigInt(value);
};
const integer = (value) => {
  const result = quantity(value);
  if (result > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("RPC integer exceeds display range");
  return Number(result);
};
const tag = (number) => `0x${number.toString(16)}`;

export function validateMarketBlock(value, expected) {
  if (!value || !HASH.test(value.hash) || !HASH.test(value.parentHash)) throw new Error("Invalid Ethereum block");
  const number = integer(value.number), timestamp = integer(value.timestamp);
  if (number < 1 || timestamp < 1 || (expected !== undefined && number !== expected)) throw new Error("Unexpected Ethereum block");
  return { number, hash: value.hash.toLowerCase(), parentHash: value.parentHash.toLowerCase(), timestamp, baseFeeWei: quantity(value.baseFeePerGas).toString() };
}

export function decodeOracleQuote(value, symbol, block) {
  if (!(symbol in MARKET_FEEDS) || typeof value !== "string" || !/^0x[0-9a-fA-F]{320}$/.test(value)) throw new Error("Invalid oracle response");
  const words = Array.from({ length: 5 }, (_, index) => BigInt(`0x${value.slice(2 + index * 64, 66 + index * 64)}`));
  const [round, answer, started, updated, answered] = words;
  if (!round || round >= (1n << 80n) || answered >= (1n << 80n) || answered < round || !answer || answer >= (1n << 255n) || started === 0n || started > updated || updated > BigInt(block.timestamp) || updated > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Invalid or incomplete oracle round");
  const updatedAt = Number(updated), ageSeconds = block.timestamp - updatedAt;
  const priceUsd = Number(answer) / 1e8;
  if (!Number.isFinite(priceUsd) || priceUsd > 1e12) throw new Error("Oracle quote exceeds display range");
  return { symbol, feed: MARKET_FEEDS[symbol], decimals: 8, answerRaw: answer.toString(), priceUsd, updatedAt, ageSeconds, status: ageSeconds <= 3600 ? "FRESH" : "STALE", roundId: round.toString(), blockNumber: block.number, blockHash: block.hash, blockTimestamp: block.timestamp };
}

async function boundedJson(response) {
  if (!response.ok) throw new Error(`Market provider HTTP ${response.status}`);
  if (Number(response.headers.get("content-length") || 0) > 262144) throw new Error("Market response exceeds limit");
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Market response is empty");
  let bytes = 0, text = "";
  const decoder = new TextDecoder();
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > 262144) { await reader.cancel(); throw new Error("Market response exceeds limit"); }
      text += decoder.decode(value, { stream: true });
    }
    text += decoder.decode();
    return JSON.parse(text);
  } finally { reader.releaseLock(); }
}

/** Fixed endpoint and methods; fetchImpl/now are dependency injection for deterministic tests. */
export function createMarketReader({ fetchImpl = globalThis.fetch, now = () => Date.now() } = {}) {
  return async function read({ signal, history = false } = {}) {
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    signal?.addEventListener("abort", abort, { once: true });
    const timer = setTimeout(abort, 25000);
    let nextId = 1;
    async function batch(calls) {
      if (calls.length < 1 || calls.length > 4) throw new Error("Market batch limit exceeded");
      const request = calls.map(([method, params]) => ({ jsonrpc: "2.0", id: nextId++, method, params }));
      const raw = await boundedJson(await fetchImpl(MARKET_RPC, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request), signal: controller.signal, credentials: "omit", cache: "no-store", redirect: "error" }));
      if (!Array.isArray(raw) || raw.length !== request.length) throw new Error("Incomplete market RPC batch");
      const ids = new Set();
      for (const item of raw) {
        if (!item || item.jsonrpc !== "2.0" || ids.has(item.id) || !request.some((call) => call.id === item.id)) throw new Error("Invalid market RPC batch identity");
        ids.add(item.id);
      }
      return request.map((call) => {
        const item = raw.find((entry) => entry.id === call.id);
        return item.error ? { error: "Provider cannot serve this observation" } : Object.hasOwn(item, "result") ? { result: item.result } : { error: "Missing RPC result" };
      });
    }
    const must = (item) => { if (item.error) throw new Error(item.error); return item.result; };
    const call = (symbol, blockTag, decimals = false) => ["eth_call", [{ to: MARKET_FEEDS[symbol], data: decimals ? "0x313ce567" : "0xfeaf968c", gas: "0x7a120" }, blockTag]];
    try {
      const first = await batch([["eth_chainId", []], ["eth_getBlockByNumber", ["latest", false]]]);
      if (must(first[0]) !== "0x1") throw new Error("Market provider is not Ethereum mainnet");
      const block = validateMarketBlock(must(first[1]));
      const observedAt = Math.floor(now() / 1000);
      if (observedAt - block.timestamp > 180 || block.timestamp > observedAt + 15) throw new Error("Market provider block is stale or future dated");
      // EIP-1898 ties calls to the observed hash, not merely a block height.
      const pinned = { blockHash: block.hash, requireCanonical: true };
      const current = await batch([call("ETH", pinned), call("BTC", pinned), call("ETH", pinned, true), call("BTC", pinned, true)]);
      const quotes = { ETH: null, BTC: null }, quoteErrors = {};
      for (const [index, symbol] of ["ETH", "BTC"].entries()) {
        try {
          if (must(current[index + 2]) !== `0x${"0".repeat(63)}8`) throw new Error("Unexpected Chainlink feed decimals");
          quotes[symbol] = decodeOracleQuote(must(current[index]), symbol, block);
        } catch (error) { quoteErrors[symbol] = error.message; }
      }
      let fees = [], feeError;
      try {
        const result = must((await batch([["eth_feeHistory", ["0x4", tag(block.number), []]]]))[0]);
        const oldest = integer(result?.oldestBlock), ratios = result?.gasUsedRatio, values = result?.baseFeePerGas;
        if (!Array.isArray(ratios) || ratios.length < 1 || ratios.length > 4 || !ratios.every((v) => Number.isFinite(v) && v >= 0 && v <= 1) || !Array.isArray(values) || values.length !== ratios.length + 1 || oldest + ratios.length - 1 !== block.number) throw new Error("Invalid fee history range");
        values.forEach(quantity);
        const headers = [];
        for (let offset = 0; offset < ratios.length; offset += 4) {
          const chunk = await batch(Array.from({ length: Math.min(4, ratios.length - offset) }, (_, i) => ["eth_getBlockByNumber", [tag(oldest + offset + i), false]]));
          chunk.forEach((entry, i) => headers.push(validateMarketBlock(must(entry), oldest + offset + i)));
        }
        headers.forEach((header, i) => {
          if (header.baseFeeWei !== quantity(values[i]).toString() || (i && (header.timestamp <= headers[i - 1].timestamp || header.parentHash !== headers[i - 1].hash)) || (i === headers.length - 1 && header.hash !== block.hash)) throw new Error("Fee history changed or has invalid order");
        });
        fees = headers.map((header) => ({ blockNumber: header.number, blockHash: header.hash, timestamp: header.timestamp, baseFeeWei: header.baseFeeWei }));
      } catch (error) { feeError = error.message; }
      const historical = { ETH: [], BTC: [], errors: [], requested: Boolean(history), mode: "sampled-blocks" };
      if (history) {
        // Sparse historical observations, not invented hourly candles. Actual timestamps come from headers.
        for (let interval = 6; interval >= 1; interval--) {
          const number = block.number - interval * 1200;
          if (number < 1) continue;
          try {
            const header = validateMarketBlock(must((await batch([["eth_getBlockByNumber", [tag(number), false]]]))[0]), number);
            if (header.timestamp >= block.timestamp) throw new Error("Invalid historical block timestamp");
            const historicalTag = { blockHash: header.hash, requireCanonical: true };
            const past = await batch([call("ETH", historicalTag), call("BTC", historicalTag), call("ETH", historicalTag, true), call("BTC", historicalTag, true)]);
            for (const [i, symbol] of ["ETH", "BTC"].entries()) {
              try {
                if (must(past[i + 2]) !== `0x${"0".repeat(63)}8`) throw new Error("Unexpected historical feed decimals");
                const point = decodeOracleQuote(must(past[i]), symbol, header);
                const previous = historical[symbol].at(-1);
                if (previous && previous.blockTimestamp >= point.blockTimestamp) throw new Error("Historical timestamp order is invalid");
                historical[symbol].push(point);
              }
              catch (error) { historical.errors.push(`${symbol} block ${number}: ${error.message}`); }
            }
          } catch (error) { historical.errors.push(`Block ${number}: ${error.message}`); }
        }
        const sampledCount = historical.ETH.length + historical.BTC.length;
        if (["ETH", "BTC"].some((symbol) => historical[symbol].length < 6)) {
          let supplemented = false;
          for (const symbol of ["ETH", "BTC"]) {
            if (historical[symbol].length >= 6) continue;
            if (!quotes[symbol]) { historical.errors.push(`${symbol}: latest round unavailable; recent rounds cannot be read`); continue; }
            const recent = [], conflictingRounds = new Set();
            const latestRound = BigInt(quotes[symbol].roundId);
            const roundInPhase = latestRound & ((1n << 64n) - 1n);
            const count = Number(roundInPhase > 6n ? 6n : roundInPhase > 1n ? roundInPhase - 1n : 0n);
            if (count < 6) historical.errors.push(`${symbol}: phase boundary limits recent-round coverage`);
            for (let offset = count; offset >= 1; offset -= 4) {
              const distances = Array.from({ length: Math.min(4, offset) }, (_, i) => offset - i);
              const results = await batch(distances.map((distance) => ["eth_call", [{ to: MARKET_FEEDS[symbol], data: `0x9a6fc8f5${(latestRound - BigInt(distance)).toString(16).padStart(64, "0")}`, gas: "0x7a120" }, pinned]]));
              results.forEach((result, i) => {
                const expectedRound = latestRound - BigInt(distances[i]);
                try {
                  const point = decodeOracleQuote(must(result), symbol, block);
                  if (point.roundId !== expectedRound.toString() || point.updatedAt >= quotes[symbol].updatedAt || (recent.length && point.updatedAt <= recent.at(-1).updatedAt)) throw new Error("Invalid recent oracle round order");
                  const archived = historical[symbol].find((sample) => sample.roundId === point.roundId);
                  if (archived && (archived.updatedAt !== point.updatedAt || archived.answerRaw !== point.answerRaw)) {
                    conflictingRounds.add(point.roundId);
                    throw new Error("Conflicting sampled and recent oracle round; both observations excluded");
                  }
                  recent.push(point);
                } catch (error) { historical.errors.push(`${symbol} round ${expectedRound}: ${error.message}`); }
              });
            }
            historical[symbol] = historical[symbol].filter((point) => !conflictingRounds.has(point.roundId));
            if (recent.length) {
              // These are returned oracle rounds, not interpolated archive prices.
              // A round can also occur in a sampled block; retain it once at its
              // actual oracle update time, with the most recent observed evidence.
              historical[symbol] = [...new Map([...historical[symbol], ...recent].map((point) => [point.updatedAt, point])).values()].sort((a, b) => a.updatedAt - b.updatedAt);
              supplemented = true;
            }
          }
          if (!sampledCount) historical.mode = "recent-oracle-rounds";
          else if (supplemented) historical.mode = "mixed-observations";
        }
      }
      const final = await batch([["eth_chainId", []], ["eth_getBlockByNumber", [tag(block.number), false]]]);
      if (must(final[0]) !== "0x1" || validateMarketBlock(must(final[1]), block.number).hash !== block.hash) throw new Error("Ethereum observation changed during read");
      if (Math.floor(now() / 1000) - block.timestamp > 180) throw new Error("Observation expired during read");
      return { source: "Chainlink Ethereum reference feeds / PublicNode", rpc: MARKET_RPC, chainId: 1, observedAt, block, quotes, quoteErrors, fees, feeError, history: historical };
    } finally { clearTimeout(timer); signal?.removeEventListener("abort", abort); }
  };
}

export const readMarket = (options) => createMarketReader()(options);

/** Reject conflicting samples; never invent points or interpolate a missing provider observation. */
export function mergeMarketSamples(previous, incoming, limit = 120) {
  if (!Array.isArray(previous) || !Array.isArray(incoming) || !Number.isInteger(limit) || limit < 1 || limit > 240) throw new Error("Invalid sample history");
  const samples = new Map();
  for (const point of [...previous, ...incoming]) {
    if (!point || !Number.isSafeInteger(point.blockNumber) || point.blockNumber < 1 || !HASH.test(point.blockHash) || !Number.isSafeInteger(point.timestamp) || point.timestamp < 1 || !/^(0|[1-9][0-9]*)$/.test(point.baseFeeWei)) throw new Error("Invalid fee sample");
    const before = samples.get(point.blockNumber);
    if (before && (before.blockHash !== point.blockHash || before.baseFeeWei !== point.baseFeeWei || before.timestamp !== point.timestamp)) throw new Error("Conflicting historical block");
    samples.set(point.blockNumber, point);
  }
  const result = [...samples.values()].sort((a, b) => a.blockNumber - b.blockNumber);
  if (result.some((point, i) => i && point.timestamp <= result[i - 1].timestamp)) throw new Error("Historical time order is invalid");
  return result.slice(-limit);
}
