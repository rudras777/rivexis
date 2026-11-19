import test from 'node:test';import assert from 'node:assert/strict';
import {marketWidgetDocument,MARKET_SYMBOLS} from './market-widget.mjs';
test('official embed has a fixed host, exact spot pair, visible attribution and no extraction API',()=>{
 for(const symbol of ['BTC','ETH'])for(const theme of ['light','dark']){
  const html=marketWidgetDocument(symbol,theme);assert.ok(html.includes(`${MARKET_SYMBOLS[symbol]}|1D`));assert.ok(html.includes('https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js'));assert.match(html,/by TradingView/);assert.match(html,/'?"showVolume":false/);assert.match(html,/'?"hideMarketStatus":false/);assert.ok(!/postMessage|fetch\(|WebSocket|localStorage|wallet|api-key/.test(html));
 }
});
test('symbols, themes, markup and upstream URLs cannot be supplied by a caller',()=>{
 for(const symbol of ['WBTC','BTCUSDT','ETH-PERP','</script><script>bad','__proto__','https://attacker.invalid'])assert.throws(()=>marketWidgetDocument(symbol));
 assert.throws(()=>marketWidgetDocument('BTC','</style>'));
});
