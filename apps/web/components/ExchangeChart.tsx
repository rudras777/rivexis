"use client";
import {useEffect,useRef,useState} from 'react';
import {marketWidgetDocument} from '@/lib/market-widget.mjs';

export function ExchangeChart(){
 const [open,setOpen]=useState(false),[visible,setVisible]=useState(true),[online,setOnline]=useState(true),[symbol,setSymbol]=useState<'BTC'|'ETH'>('BTC'),[theme,setTheme]=useState<'light'|'dark'>('dark'),[revision,setRevision]=useState(0),[notice,setNotice]=useState('');
 const lastReload=useRef(0);
 useEffect(()=>{
  const update=()=>{setVisible(!document.hidden);setOnline(navigator.onLine);setTheme(document.documentElement.dataset.theme==='light'?'light':'dark')};update();
  document.addEventListener('visibilitychange',update);window.addEventListener('online',update);window.addEventListener('offline',update);window.addEventListener('rivexis-appearance-change',update);
  return()=>{document.removeEventListener('visibilitychange',update);window.removeEventListener('online',update);window.removeEventListener('offline',update);window.removeEventListener('rivexis-appearance-change',update)};
 },[]);
 const mounted=open&&visible&&online;
 return <details className="exchangeChart" onToggle={e=>setOpen(e.currentTarget.open)}><summary>Exchange market chart <span className="muted">· TradingView</span></summary>
 <p>Bitstamp spot {symbol} / USD. {symbol==='BTC'?'Bitcoin, not wrapped Bitcoin.':'Ether, not wrapped Ether.'} Exchange prices provide market context; LiquidationGuard uses each protocol’s validated oracle.</p>
 <div className="exchangeChartControls"><label className="field">Market pair<select value={symbol} onChange={e=>setSymbol(e.target.value as 'BTC'|'ETH')}><option value="BTC">BTC / USD · Bitstamp spot</option><option value="ETH">ETH / USD · Bitstamp spot</option></select></label><button className="ghost" type="button" disabled={!mounted} onClick={()=>{if(Date.now()-lastReload.current<15000){setNotice('Wait 15 seconds before reloading the chart.');return}lastReload.current=Date.now();setNotice('Chart reloaded. Source timestamps and availability are controlled by TradingView.');setRevision(n=>n+1)}}>Reload exchange chart</button></div>
 {/* A data URL has an opaque origin, even with allow-same-origin. Never replace
     it with srcDoc or an application URL: the official nested widget needs its
     own origin for cookies, but its loader must never share the app origin. */}
 {mounted?<iframe key={`${symbol}:${theme}:${revision}`} className="exchangeChartFrame" title={`${symbol} / USD · Bitstamp spot · TradingView`} src={`data:text/html;charset=utf-8,${encodeURIComponent(marketWidgetDocument(symbol,theme))}`} sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox" referrerPolicy="no-referrer" loading="lazy"/>:<p role="status">{!online?'Exchange chart unavailable while offline.':!visible?'Exchange chart paused while this tab is hidden.':'Open to load the provider’s display.'}</p>}
 <p className="muted">Provider-managed display, loaded from TradingView when opened. Source timestamps, market status and any delays appear inside the chart. Rivexis cannot independently verify its freshness. If the chart is blank or unavailable, use Reload or <a href={`https://www.tradingview.com/symbols/${symbol}USD/?exchange=BITSTAMP`} target="_blank" rel="noopener noreferrer">view on TradingView</a>. No exchange data is copied into calculations or exports.</p>{notice&&<p role="status">{notice}</p>}
 </details>;
}
