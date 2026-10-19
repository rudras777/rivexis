import {test,expect} from '@playwright/test';
import {writeFile} from 'node:fs/promises';

for(const mobile of [false,true])test(`Shared blockchain background measured with fourfold CPU throttling: ${mobile?'mobile':'desktop'}`,async({page,context},testInfo)=>{
 await page.setViewportSize(mobile?{width:390,height:844}:{width:1440,height:900});
 const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{
  const metrics={lcp:0,lcpElement:"",cls:0,longTasks:0,longTaskTime:0,draws:0};Object.assign(window,{blockchainMeasured:metrics});
  for(const type of ['largest-contentful-paint','layout-shift','longtask'])try{new PerformanceObserver(list=>{for(const entry of list.getEntries()){
   if(type==='largest-contentful-paint'){metrics.lcp=entry.startTime;metrics.lcpElement=(entry as PerformanceEntry&{element?:Element}).element?.tagName||'';}
   if(type==='layout-shift'&&!(entry as PerformanceEntry&{hadRecentInput:boolean}).hadRecentInput)metrics.cls+=(entry as PerformanceEntry&{value:number}).value;
   if(type==='longtask'){metrics.longTasks++;metrics.longTaskTime+=entry.duration;}
  }}).observe({type,buffered:true})}catch{}
  const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,...args:unknown[]){const result=Reflect.apply(original,this,args);if(args[0]==='webgl'&&result){const gl=result as WebGLRenderingContext,draw=gl.drawArrays.bind(gl);gl.drawArrays=(mode,first,count)=>{draw(mode,first,count);metrics.draws++}}return result} as typeof original;
 });
 await page.goto('/');
 await page.waitForTimeout(1000);const start=await page.evaluate(()=>(window as unknown as {blockchainMeasured:{draws:number}}).blockchainMeasured.draws);await page.waitForTimeout(1000);
 const measured=await page.evaluate(()=>({...(window as unknown as {blockchainMeasured:{draws:number;lcp:number;lcpElement:string;cls:number;longTasks:number;longTaskTime:number}}).blockchainMeasured,navigation:performance.getEntriesByType('navigation').map(e=>({ttfb:(e as PerformanceNavigationTiming).responseStart,responseEnd:(e as PerformanceNavigationTiming).responseEnd,domContentLoaded:(e as PerformanceNavigationTiming).domContentLoadedEventEnd,loadEventEnd:(e as PerformanceNavigationTiming).loadEventEnd})),paint:performance.getEntriesByType('paint').map(e=>({name:e.name,startTime:e.startTime})),fontStatus:document.fonts.status,resources:performance.getEntriesByType('resource').map(entry=>({name:new URL(entry.name).pathname,transferSize:(entry as PerformanceResourceTiming).transferSize,duration:entry.duration,startTime:entry.startTime,responseEnd:(entry as PerformanceResourceTiming).responseEnd,initiatorType:(entry as PerformanceResourceTiming).initiatorType})),overflow:document.documentElement.scrollWidth>innerWidth}));
 // Keep selector/DOM traversal outside the paint-measurement window.
 await expect(page.locator('.blockchainBackground')).toHaveCount(1);await expect(page.locator('canvas,.riskAtlas')).toHaveCount(0);
 const draws=measured.draws-start;expect(draws).toBeLessThanOrEqual(125);expect(draws).toBe(0);expect(measured.overflow).toBe(false);expect(errors).toEqual([]);
 await page.screenshot({path:`../../../../outputs/cinematic-atmosphere-measured-${mobile?'mobile':'desktop'}.png`});
 await writeFile(`../../../../outputs/CINEMATIC_ATMOSPHERE_${mobile?'MOBILE':'DESKTOP'}_MEASUREMENTS.json`,JSON.stringify({measuredAt:new Date().toISOString(),url:page.url(),cpuThrottling:4,traceMode:testInfo.project.use.trace,videoMode:testInfo.project.use.video,fieldData:false,lighthouse:false,drawsInObservedSecond:draws,errors,...measured},null,2));
});
