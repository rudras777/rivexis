import {test,expect} from '@playwright/test';
import {writeFile} from 'node:fs/promises';

for(const mobile of [false,true])test(`Shared blockchain background measured with fourfold CPU throttling: ${mobile?'mobile':'desktop'}`,async({page,context})=>{
 await page.setViewportSize(mobile?{width:390,height:844}:{width:1440,height:900});
 const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.addInitScript(()=>{
  const metrics={lcp:0,cls:0,longTasks:0,longTaskTime:0,draws:0};Object.assign(window,{atlasMeasured:metrics});
  for(const type of ['largest-contentful-paint','layout-shift','longtask'])try{new PerformanceObserver(list=>{for(const entry of list.getEntries()){
   if(type==='largest-contentful-paint')metrics.lcp=entry.startTime;
   if(type==='layout-shift'&&!(entry as PerformanceEntry&{hadRecentInput:boolean}).hadRecentInput)metrics.cls+=(entry as PerformanceEntry&{value:number}).value;
   if(type==='longtask'){metrics.longTasks++;metrics.longTaskTime+=entry.duration;}
  }}).observe({type,buffered:true})}catch{}
  const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,...args:unknown[]){const result=Reflect.apply(original,this,args);if(args[0]==='webgl'&&result){const gl=result as WebGLRenderingContext,draw=gl.drawArrays.bind(gl);gl.drawArrays=(mode,first,count)=>{draw(mode,first,count);metrics.draws++}}return result} as typeof original;
 });
 await page.goto('/');await expect(page.locator('.blockchainBackground')).toHaveCount(1);await expect(page.locator('canvas,.riskAtlas')).toHaveCount(0);
 await page.waitForTimeout(1000);const start=await page.evaluate(()=>(window as unknown as {atlasMeasured:{draws:number}}).atlasMeasured.draws);await page.waitForTimeout(1000);
 const measured=await page.evaluate(()=>({...(window as unknown as {atlasMeasured:{draws:number;lcp:number;cls:number;longTasks:number;longTaskTime:number}}).atlasMeasured,resources:performance.getEntriesByType('resource').map(entry=>({name:new URL(entry.name).pathname,transferSize:(entry as PerformanceResourceTiming).transferSize,duration:entry.duration})),overflow:document.documentElement.scrollWidth>innerWidth}));
 const draws=measured.draws-start;expect(draws).toBeLessThanOrEqual(125);expect(draws).toBe(0);expect(measured.overflow).toBe(false);expect(errors).toEqual([]);
 await page.screenshot({path:`../../../../outputs/mesh-removal-measured-${mobile?'mobile':'desktop'}.png`});
 await writeFile(`../../../../outputs/BLOCKCHAIN_BACKGROUND_${mobile?'MOBILE':'DESKTOP'}_MEASUREMENTS.json`,JSON.stringify({measuredAt:new Date().toISOString(),url:page.url(),cpuThrottling:4,fieldData:false,lighthouse:false,drawsInObservedSecond:draws,errors,...measured},null,2));
});
