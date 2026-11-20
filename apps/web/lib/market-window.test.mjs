import test from 'node:test';
import assert from 'node:assert/strict';
import {mergeOracleSamples,mergeMarketWindow,MARKET_FEEDS} from './market-feed.mjs';
const hash=n=>'0x'+n.toString(16).padStart(64,'0');
const quote=(n=1)=>({symbol:'ETH',feed:MARKET_FEEDS.ETH,answerRaw:'100000000',priceUsd:1,roundId:String(n),updatedAt:1800000000+n,blockNumber:n,blockHash:hash(n),blockTimestamp:1800000000+n,decimals:8,status:'FRESH',ageSeconds:0});
const snapshot=(n=2)=>({block:{number:n,hash:hash(n),parentHash:hash(n-1)},quotes:{ETH:quote(n),BTC:null},history:{ETH:[],BTC:[]},fees:[{blockNumber:n,blockHash:hash(n),timestamp:1800000000+n,baseFeeWei:'1'}]});
test('oracle window deduplicates rounds, retains exact answers and rejects conflicting rounds and timestamp aliases',()=>{
 const q=quote();assert.equal(mergeOracleSamples([q],[{...q,blockNumber:2,blockHash:hash(2)}]).length,1);
 assert.throws(()=>mergeOracleSamples([q],[{...q,answerRaw:'100000001'}]),/Conflicting/);
 assert.throws(()=>mergeOracleSamples([q],[{...q,roundId:'2',answerRaw:'2'}]),/Conflicting/);
 assert.equal(mergeOracleSamples([],Array.from({length:150},(_,i)=>quote(i+1)),96).length,96);
});
test('older provider heads cannot replace newer evidence; detected reorg clears both price and fee history',()=>{
 const previous=snapshot(2),next=snapshot(3),retained={ETH:[quote()],BTC:[]};
 assert.throws(()=>mergeMarketWindow(previous,snapshot(1),previous.fees,retained),/Older/);
 next.block.parentHash=hash(100);const merged=mergeMarketWindow(previous,next,previous.fees,retained);
 assert.equal(merged.reset,true);assert.equal(merged.quotes.ETH.length,1);assert.equal(merged.quotes.ETH[0].blockNumber,3);assert.equal(merged.fees.length,1);
});
test('overlapping fee conflict invalidates retained quote observations as well',()=>{
 const previous=snapshot(2),next=snapshot(2);next.fees[0].baseFeeWei='2';
 const merged=mergeMarketWindow(previous,next,previous.fees,{ETH:[quote()],BTC:[]});assert.equal(merged.reset,true);assert.equal(merged.quotes.ETH.length,1);
});
