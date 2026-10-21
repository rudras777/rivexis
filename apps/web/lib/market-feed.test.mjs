import test from "node:test";
import assert from "node:assert/strict";
import { createMarketReader, decodeOracleQuote, validateMarketBlock, mergeMarketSamples, MARKET_FEEDS, MARKET_RPC } from "./market-feed.mjs";
const time = 1800000000, head = 30000000;
const hash = (number) => `0x${BigInt(number).toString(16).padStart(64, "0")}`;
const hex = (number) => `0x${number.toString(16)}`;
const word = (number) => BigInt(number).toString(16).padStart(64, "0");
const round = (timestamp, answer = 300000000000n, id = 10n, answered = id) => `0x${[id, answer, timestamp - 1, timestamp, answered].map(word).join("")}`;
const block = (number = head) => ({ number: hex(number), hash: hash(number), parentHash: hash(number - 1), timestamp: hex(time - (head - number) * 12), baseFeePerGas: "0x3b9aca00" });
function fixture(change = () => {}) {
  const calls = [];
  const fetchImpl = async (url, init) => {
    assert.equal(url, MARKET_RPC); assert.equal(init.credentials, "omit");
    if (init.signal.aborted) throw new DOMException("Aborted", "AbortError");
    const request = JSON.parse(init.body); assert.ok(request.length <= 4);
    const results = request.map((call) => {
      calls.push(call);
      let result;
      if (call.method === "eth_chainId") result = "0x1";
      else if (call.method === "eth_getBlockByNumber") result = block(call.params[0] === "latest" ? head : Number(BigInt(call.params[0])));
      else if (call.method === "eth_feeHistory") result = { oldestBlock: hex(head - 3), baseFeePerGas: Array(5).fill("0x3b9aca00"), gasUsedRatio: Array(4).fill(0.5) };
      else if (call.method === "eth_call") {
        assert.ok(Object.values(MARKET_FEEDS).includes(call.params[0].to));
        assert.equal(call.params[1].requireCanonical, true);
        const number = Number(BigInt(call.params[1].blockHash));
        const requestedRound = call.params[0].data.startsWith("0x9a6fc8f5") ? BigInt(`0x${call.params[0].data.slice(10)}`) : 10n;
        result = call.params[0].data === "0x313ce567" ? `0x${word(8)}` : round(time - (head - number) * 12 - 60 - Number(10n - requestedRound) * 600, 300000000000n, requestedRound);
      } else assert.fail("Unapproved RPC method");
      const response = { jsonrpc: "2.0", id: call.id, result };
      change(response, call, calls);
      return response;
    }).reverse();
    return new Response(JSON.stringify(results), { headers: { "Content-Type": "application/json" } });
  };
  return { read: createMarketReader({ fetchImpl, now: () => time * 1000 }), calls };
}
test("fresh genuine-shape pinned quotes and four actual fee headers", async () => {
  const data = await fixture().read();
  assert.equal(data.quotes.ETH.priceUsd, 3000); assert.equal(data.quotes.BTC.status, "FRESH");
  assert.equal(data.fees.length, 4); assert.equal(data.fees.at(-1).timestamp, time);
});
test("24-hour sparse history uses actual timestamp and block provenance", async () => {
  const data = await fixture().read({ history: true });
  assert.equal(data.history.ETH.length, 6); assert.equal(data.history.ETH[0].blockTimestamp, time - 86400);
  assert.equal(data.history.errors.length, 0);
});
test("wrong network fails closed before price reads", async () => {
  const f = fixture((r, c) => { if (c.method === "eth_chainId") r.result = "0x2"; });
  await assert.rejects(f.read(), /not Ethereum/); assert.equal(f.calls.length, 2);
});
test("stale network block fails closed", async () => {
  await assert.rejects(fixture((r, c) => { if (c.method === "eth_getBlockByNumber") r.result.timestamp = hex(time - 181); }).read(), /stale/);
});
test("future network block fails closed", async () => {
  await assert.rejects(fixture((r, c) => { if (c.method === "eth_getBlockByNumber") r.result.timestamp = hex(time + 16); }).read(), /future/);
});
test("old oracle answer is labeled STALE with actual update time", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_call" && c.params[0].data === "0xfeaf968c") r.result = round(time - 3601); }).read();
  assert.equal(data.quotes.ETH.status, "STALE"); assert.equal(data.quotes.ETH.ageSeconds, 3601);
});
test("negative and zero prices are unavailable, never a fake zero success", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_call" && c.params[0].data === "0xfeaf968c") r.result = round(time - 1, c.params[0].to === MARKET_FEEDS.ETH ? (1n << 256n) - 1n : 0n); }).read();
  assert.equal(data.quotes.ETH, null); assert.equal(data.quotes.BTC, null); assert.ok(data.quoteErrors.ETH);
});
test("incomplete and future oracle rounds are rejected", () => {
  const b = validateMarketBlock(block());
  assert.throws(() => decodeOracleQuote(round(time, 1n, 10n, 9n), "ETH", b), /incomplete/);
  assert.throws(() => decodeOracleQuote(round(time + 1), "BTC", b), /incomplete/);
});
test("feed decimals must be checked instead of assumed", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_call" && c.params[0].data === "0x313ce567") r.result = `0x${word(18)}`; }).read();
  assert.equal(data.quotes.ETH, null); assert.match(data.quoteErrors.ETH, /decimals/);
});
test("archive failures leave gaps with truthful messages", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_call" && Number(BigInt(c.params[1].blockHash)) < head) { delete r.result; r.error = { code: -32000 }; } }).read({ history: true });
  assert.equal(data.history.mode, "recent-oracle-rounds"); assert.equal(data.history.ETH.length, 6); assert.equal(data.history.errors.length, 12); assert.equal(data.quotes.ETH.status, "FRESH");
});
test("reorg of final observed block rejects entire observation", async () => {
  await assert.rejects(fixture((r, c, calls) => { if (c.method === "eth_getBlockByNumber" && calls.filter((v) => v.method === "eth_chainId").length === 2) r.result.hash = hash(head + 1); }).read(), /changed/);
});
test("malformed fee range does not produce a fabricated graph", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_feeHistory") r.result.baseFeePerGas.pop(); }).read();
  assert.deepEqual(data.fees, []); assert.match(data.feeError, /range/);
});
test("fee header mismatch is reported rather than accepted", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_feeHistory") r.result.baseFeePerGas[0] = "0x1"; }).read();
  assert.deepEqual(data.fees, []); assert.match(data.feeError, /changed/);
});
test("abort and provider transport failure reject", async () => {
  const controller = new AbortController(); controller.abort();
  await assert.rejects(fixture().read({ signal: controller.signal }), /Aborted/);
  await assert.rejects(createMarketReader({ fetchImpl: async () => { throw new Error("offline"); } })(), /offline/);
});
test("HTTP rate limits and oversized responses reject", async () => {
  await assert.rejects(createMarketReader({ fetchImpl: async () => new Response("limited", { status: 429 }) })(), /429/);
  await assert.rejects(createMarketReader({ fetchImpl: async () => new Response("[]", { headers: { "Content-Length": "262145" } }) })(), /limit/);
});
test("missing or duplicate batch identities reject", async () => {
  await assert.rejects(createMarketReader({ fetchImpl: async () => new Response("[]") })(), /Incomplete/);
  await assert.rejects(fixture((r) => { r.id = 1; }).read(), /identity/);
});
test("repeated fee history deduplicates, preserves real gaps and bounded size", () => {
  const a = { blockNumber: 1, blockHash: hash(1), timestamp: 1, baseFeeWei: "0" };
  const b = { blockNumber: 3, blockHash: hash(3), timestamp: 3, baseFeeWei: "2" };
  assert.deepEqual(mergeMarketSamples([a], [b, a]), [a, b]);
  assert.deepEqual(mergeMarketSamples([a], [b], 1), [b]);
  assert.throws(() => mergeMarketSamples([a], [{ ...a, blockHash: hash(2) }]), /Conflicting/);
});
test("malformed header fields never enter observed history", () => {
  assert.throws(() => validateMarketBlock({ ...block(), number: "0x00" }), /integer/);
  assert.throws(() => validateMarketBlock({ ...block(), hash: "0x1234" }), /block/);
});
test("recent-round fallback preserves genuine update timestamps", async () => {
  const data = await fixture((r, c) => { if (c.method === "eth_call" && Number(BigInt(c.params[1].blockHash)) < head) { delete r.result; r.error = { code: -32000 }; } }).read({ history: true });
  assert.equal(data.history.mode, "recent-oracle-rounds");
  assert.deepEqual(data.history.ETH.map((p) => p.roundId), ["4", "5", "6", "7", "8", "9"]);
  assert.equal(data.history.ETH[0].updatedAt, time - 3660);
  assert.equal(data.history.ETH[0].blockTimestamp, time);
});
test("recent-round reverts and conflicting timestamps leave explicit gaps", async () => {
  const data = await fixture((r, c) => {
    if (c.method !== "eth_call") return;
    if (Number(BigInt(c.params[1].blockHash)) < head) { delete r.result; r.error = { code: -32000 }; }
    if (c.params[0].data.startsWith("0x9a6fc8f5")) r.result = round(time - 60);
  }).read({ history: true });
  assert.deepEqual(data.history.ETH, []);
  assert.equal(data.history.errors.length, 24);
});
test("recent round fallback does not cross phase boundaries", async () => {
  const data = await fixture((r, c) => {
    if (c.method !== "eth_call") return;
    if (Number(BigInt(c.params[1].blockHash)) < head) { delete r.result; r.error = { code: -32000 }; }
    if (c.params[0].data === "0xfeaf968c" && Number(BigInt(c.params[1].blockHash)) === head) r.result = round(time - 60, 1n, (2n << 64n) + 1n);
  }).read({ history: true });
  assert.deepEqual(data.history.ETH, []);
  assert.ok(data.history.errors.some((e) => e.includes("phase boundary")));
});

const recentCall = c => c.method === 'eth_call' && c.params[0].data.startsWith('0x9a6fc8f5');
function partialHistory(symbols=['ETH','BTC'],extra=()=>{}){
 return fixture((response,call,calls)=>{
  if(call.method==='eth_call'&&Number(BigInt(call.params[1].blockHash))<head-2400&&symbols.some(s=>call.params[0].to===MARKET_FEEDS[s])){delete response.result;response.error={code:-32000}}
  extra(response,call,calls);
 });
}
for(const symbol of ['ETH','BTC'])test(`partial ${symbol} archive history supplements only that feed`,async()=>{
 const other=symbol==='ETH'?'BTC':'ETH';const f=partialHistory([symbol]);const data=await f.read({history:true});
 assert.equal(data.history.mode,'mixed-observations');assert.equal(data.history[symbol].length,8);assert.equal(data.history[other].length,6);
 assert.equal(f.calls.filter(c=>recentCall(c)&&c.params[0].to===MARKET_FEEDS[symbol]).length,6);assert.equal(f.calls.filter(c=>recentCall(c)&&c.params[0].to===MARKET_FEEDS[other]).length,0);
 assert.equal(data.history.errors.length,4);
});
test('both partial histories preserve sampled points and supplement actual rounds in timestamp order',async()=>{
 const data=await partialHistory().read({history:true});assert.equal(data.history.mode,'mixed-observations');
 for(const symbol of ['ETH','BTC']){assert.equal(data.history[symbol].length,8);assert.ok(data.history[symbol].some(p=>p.blockNumber<head));assert.ok(data.history[symbol].some(p=>p.blockNumber===head));assert.ok(data.history[symbol].every((p,i,a)=>!i||p.updatedAt>a[i-1].updatedAt))}
 assert.equal(data.history.errors.length,8);
});
test('a feed with no archive coverage recovers even when the other archive is complete',async()=>{
 const f=fixture((r,c)=>{if(c.method==='eth_call'&&c.params[0].to===MARKET_FEEDS.ETH&&Number(BigInt(c.params[1].blockHash))<head){delete r.result;r.error={code:-32000}}});
 const data=await f.read({history:true});assert.equal(data.history.mode,'mixed-observations');assert.equal(data.history.ETH.length,6);assert.equal(data.history.BTC.length,6);assert.equal(f.calls.filter(c=>recentCall(c)&&c.params[0].to===MARKET_FEEDS.BTC).length,0);
});
test('complete archive coverage spends no supplemental round calls',async()=>{
 const f=fixture();const data=await f.read({history:true});assert.equal(data.history.mode,'sampled-blocks');assert.equal(f.calls.filter(recentCall).length,0);
});
test('supplement provider errors retain partial observations and disclose every rejected round',async()=>{
 const data=await partialHistory(['ETH','BTC'],(r,c)=>{if(recentCall(c)){delete r.result;r.error={code:-32000}}}).read({history:true});
 assert.equal(data.history.ETH.length,2);assert.equal(data.history.BTC.length,2);assert.equal(data.history.mode,'sampled-blocks');assert.equal(data.history.errors.length,20);
});
test('wrong returned supplemental round cannot fill a partial archive gap',async()=>{
 const data=await partialHistory(['ETH','BTC'],(r,c)=>{if(recentCall(c))r.result=round(time-60)}).read({history:true});
 assert.equal(data.history.ETH.length,2);assert.equal(data.history.BTC.length,2);assert.equal(data.history.errors.length,20);assert.ok(data.history.errors.some(e=>e.includes('recent oracle round')));
});
test('partial archive supplement respects a new aggregator phase boundary',async()=>{
 const f=partialHistory(['ETH','BTC'],(r,c)=>{if(c.method==='eth_call'&&c.params[0].data==='0xfeaf968c'&&Number(BigInt(c.params[1].blockHash))===head)r.result=round(time-60,1n,(2n<<64n)+1n)});
 const data=await f.read({history:true});assert.equal(data.history.ETH.length,2);assert.equal(f.calls.filter(recentCall).length,0);assert.ok(data.history.errors.some(e=>e.includes('phase boundary')));
});
test('overlapping sampled and recent observations are deduplicated by actual oracle update time',async()=>{
 const data=await partialHistory(['ETH'],(r,c)=>{
  if(c.method!=='eth_call'||c.params[0].to!==MARKET_FEEDS.ETH)return;
  if(recentCall(c)){const id=BigInt('0x'+c.params[0].data.slice(10));r.result=round(time-60-Number(10n-id)*3600,300000000000n,id)}
  else if(c.params[0].data==='0xfeaf968c'&&Number(BigInt(c.params[1].blockHash))===head-1200)r.result=round(time-14460,300000000000n,6n);
 }).read({history:true});
 assert.equal(data.history.ETH.length,7);assert.equal(new Set(data.history.ETH.map(p=>p.updatedAt)).size,7);assert.equal(data.history.ETH.find(p=>p.updatedAt===time-14460).blockNumber,head);
});
test('supplemental timestamps newer than the latest validated round remain unavailable',async()=>{
 const data=await partialHistory(['ETH','BTC'],(r,c)=>{if(recentCall(c))r.result=round(time-30,300000000000n,BigInt('0x'+c.params[0].data.slice(10)))}).read({history:true});
 assert.equal(data.history.ETH.length,2);assert.equal(data.history.BTC.length,2);assert.equal(data.history.errors.length,20);
});
test('ordinary quote polling does not backfill history or spend supplemental calls',async()=>{
 const f=partialHistory();const data=await f.read();assert.equal(data.history.requested,false);assert.equal(f.calls.filter(recentCall).length,0);assert.equal(f.calls.length,13);
});

test('same-round conflicts exclude both ambiguous observations instead of choosing a source',async()=>{
 const data=await partialHistory(['ETH'],(r,c)=>{
  if(c.method==='eth_call'&&c.params[0].to===MARKET_FEEDS.ETH&&c.params[0].data==='0xfeaf968c'&&Number(BigInt(c.params[1].blockHash))===head-1200)r.result=round(time-14460,200000000000n,6n);
 }).read({history:true});
 assert.equal(data.history.ETH.find(p=>p.roundId==='6'),undefined);assert.ok(data.history.errors.some(e=>e.includes('both observations excluded')));
});
