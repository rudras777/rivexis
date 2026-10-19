import {test as base,expect,type Page,type Request,type Response} from '@playwright/test';
import {runGuardedNavigation} from './navigation-driver-policy.mjs';
export {expect};
export type * from '@playwright/test';

const installed=new WeakSet<Page>();
function guardFirefoxPage(page:Page){
  if(installed.has(page))return;installed.add(page);
  const goto=page.goto.bind(page),reload=page.reload.bind(page);
  async function navigate(url:string,options:Parameters<Page['goto']>[1],initial:(options:Parameters<Page['goto']>[1])=>ReturnType<Page['goto']>){
    const info=base.info(),baseURL=info.project.use.baseURL;
    let target:string;try{target=new URL(url,baseURL??page.url()).href}catch{return initial(options)}
    const before=await page.evaluate(()=>({href:location.href,timeOrigin:performance.timeOrigin}));
    const pending=new Set<Request>();let pageErrors=0,resourceFailures=0,serverFailures=0,documentStatus=0;
    const request=(r:Request)=>pending.add(r),finished=(r:Request)=>pending.delete(r);
    const failed=(r:Request)=>{pending.delete(r);if(new URL(r.url()).origin===new URL(target).origin)resourceFailures++};
    const error=()=>{pageErrors++};
    const response=(r:Response)=>{const request=r.request();if(new URL(r.url()).origin===new URL(target).origin&&r.status()>=500)serverFailures++;if(request.isNavigationRequest()&&request.frame()===page.mainFrame()&&r.url()===target)documentStatus=r.status()};
    page.on('request',request);page.on('requestfinished',finished);page.on('requestfailed',failed);page.on('pageerror',error);page.on('response',response);
    const timeout=Math.min(options?.timeout&&options.timeout>0?options.timeout:15000,15000);
    try{
      return await runGuardedNavigation({
        initial:()=>initial({...options,timeout}),
        inspect:async()=>{
        const state=await page.evaluate(()=>({href:location.href,timeOrigin:performance.timeOrigin,readyState:document.readyState,mainPresent:!!document.querySelector('main'),buildPresent:!!document.querySelector('meta[name="rivexis-build"]')})).catch(()=>null);
        return state&&{...state,browserName:'firefox',expectedOrigin:new URL(baseURL??before.href).origin,target,previousHref:before.href,previousTimeOrigin:before.timeOrigin,documentStatus,pending:pending.size,pageErrors,resourceFailures,serverFailures};
        },
        record:evidence=>{
        // No test or application action is retried. Only a safe bare GET may supersede
        // the stuck driver operation; every subsequent test assertion still executes.
        const description=JSON.stringify({target,documentStatus,readyState:evidence.readyState,pending:pending.size,pageErrors,resourceFailures,serverFailures});
        info.annotations.push({type:'firefox-driver-navigation-release',description});
        console.warn('FIREFOX_DRIVER_NAVIGATION_RELEASE '+description);
        },
        release:()=>goto(target,{...options,timeout}),
      });
    }finally{page.off('request',request);page.off('requestfinished',finished);page.off('requestfailed',failed);page.off('pageerror',error);page.off('response',response)}
  }
  page.goto=(url,options)=>navigate(url,options,next=>goto(url,next));
  page.reload=options=>navigate(page.url(),options,next=>reload(next));
}

// Isolated Playwright-owned test contexts only; no production code, browser binary,
// application error handler, clock, wallet or authentication state is modified.
export const test=base.extend({browser:[async({browser,browserName},use)=>{
  if(browserName!=='firefox'){await use(browser);return}
  const create=browser.newContext.bind(browser);
  browser.newContext=async options=>{const context=await create(options);context.on('page',guardFirefoxPage);return context};
  try{await use(browser)}finally{browser.newContext=create}
},{scope:'worker'}]});
