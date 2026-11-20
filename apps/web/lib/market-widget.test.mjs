import test from 'node:test';import assert from 'node:assert/strict';import {runInNewContext} from 'node:vm';
import {marketWidgetDocument,MARKET_SYMBOLS} from './market-widget.mjs';
test('official embed has a fixed host, exact spot pair, visible attribution and no extraction API',()=>{
 for(const symbol of ['BTC','ETH'])for(const theme of ['light','dark']){
  const html=marketWidgetDocument(symbol,theme);assert.ok(html.includes(`${MARKET_SYMBOLS[symbol]}|1D`));assert.ok(html.includes('https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js'));assert.match(html,/by TradingView/);const result=bootstrap(html,true);assert.equal(result.loads.length,1);const config=JSON.parse(result.loads[0].textContent);assert.equal(config.showVolume,false);assert.equal(config.hideMarketStatus,false);assert.ok(!/postMessage|fetch\(|WebSocket|localStorage|wallet|api-key/.test(html));
 }
});
test('symbols, themes, markup and upstream URLs cannot be supplied by a caller',()=>{
 for(const symbol of ['WBTC','BTCUSDT','ETH-PERP','</script><script>bad','__proto__','https://attacker.invalid'])assert.throws(()=>marketWidgetDocument(symbol));
 assert.throws(()=>marketWidgetDocument('BTC','</style>'));
});

function bootstrap(html,isolated){
 const loads=[],message={textContent:''},parent={};if(isolated)Object.defineProperty(parent,'document',{get(){throw new Error('SecurityError')}});else parent.document={};
 runInNewContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],{parent,document:{createElement:()=>({}),querySelector:selector=>selector.endsWith('__widget')?message:{appendChild:script=>loads.push(script)}}});
 return {loads,message:message.textContent};
}
test('bootstrap refuses every provider script when the browser exposes the parent document',()=>{
 const result=bootstrap(marketWidgetDocument(),false);assert.equal(result.loads.length,0);assert.match(result.message,/unavailable.*could not isolate/);
 const isolated=bootstrap(marketWidgetDocument(),true);assert.equal(isolated.loads[0].src,'https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js');
});
