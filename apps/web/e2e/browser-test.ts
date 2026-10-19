import {test as base,expect,type Page,type Request,type Response} from '@playwright/test';
import {mayReleaseStrandedNavigation,runGuardedNavigation} from './navigation-driver-policy.mjs';
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
    const pending=new Set<Request>();let pageErrors=0,resourceFailures=0,serverFailures=0,documentStatus=0,documentRequests=0;
    const request=(r:Request)=>{pending.add(r);if(r.isNavigationRequest()&&r.frame()===page.mainFrame())documentRequests++},finished=(r:Request)=>pending.delete(r);
    const failed=(r:Request)=>{pending.delete(r);resourceFailures++};
    const error=()=>{pageErrors++};
    const response=(r:Response)=>{const request=r.request();if(r.status()>=500)serverFailures++;if(request.isNavigationRequest()&&request.frame()===page.mainFrame()&&r.url()===target)documentStatus=r.status()};
    page.on('request',request);page.on('requestfinished',finished);page.on('requestfailed',failed);page.on('pageerror',error);page.on('response',response);
    const timeout=Math.min(options?.timeout&&options.timeout>0?options.timeout:15000,15000);
    try{
      return await runGuardedNavigation({
        initial:()=>initial({...options,timeout}),
        inspect:async()=>{
        const state=await page.evaluate(()=>({href:location.href,timeOrigin:performance.timeOrigin,readyState:document.readyState,contentPresent:!!document.querySelector('main')||(location.pathname==='/app'&&!!document.querySelector('.defiWorkspace h1')&&!!document.querySelector('.defiWorkspace .lookupBar[aria-label="Wallet inspection"] input#wallet-address')),buildPresent:!!document.querySelector('meta[name="rivexis-build"]')})).catch(()=>null);
        const evidence=state&&{...state,browserName:'firefox',expectedOrigin:new URL(baseURL??before.href).origin,target,previousHref:before.href,previousTimeOrigin:before.timeOrigin,documentStatus,pending:pending.size,pageErrors,resourceFailures,serverFailures};
        // Diagnostic paths exclude credentials/query/fragment; no response bodies,
        // cookies, storage, browser logs or financial data are captured here.
        const path=(href:string)=>{try{const u=new URL(href);return u.origin+u.pathname}catch{return 'unavailable'}};
        console.warn('FIREFOX_NAVIGATION_TIMEOUT_EVIDENCE '+JSON.stringify({target:path(target),href:state?path(state.href):null,documentRequests,documentStatus,pending:pending.size,pageErrors,resourceFailures,serverFailures,readyState:state?.readyState,contentPresent:state?.contentPresent,buildPresent:state?.buildPresent,newDocument:!!state&&(before.href!==state.href||before.timeOrigin!==state.timeOrigin),releaseEligible:!!evidence&&mayReleaseStrandedNavigation(evidence)}));
        return evidence;
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
export const test=base.extend({browser:[async({browser,browserName},use,workerInfo)=>{
  const hostname=new URL(workerInfo.project.use.baseURL??'http://127.0.0.1:3000').hostname;
  const local=['localhost','127.0.0.1','[::1]'].includes(hostname);
  if(browserName!=='firefox'&&!local){await use(browser);return}
  const create=browser.newContext.bind(browser);
  browser.newContext=async options=>{
    const context=await create(options);
    // Local functional fixtures never spend a real provider allowance. Dedicated
    // market page.route fixtures take precedence; real-public suites are excluded.
    if(local)await context.route('https://ethereum.publicnode.com/**',async route=>{
      const headers={'access-control-allow-origin':'*','access-control-allow-methods':'POST, OPTIONS','access-control-allow-headers':'content-type'};
      if(route.request().method()==='OPTIONS'){await route.fulfill({status:204,headers});return}
      const request=route.request().postDataJSON();
      const unavailable=(r:{id?:unknown})=>({jsonrpc:'2.0',id:r.id??null,error:{code:-32000,message:'Market provider intentionally unavailable in isolated local fixture'}});
      await route.fulfill({headers,json:Array.isArray(request)?request.map(unavailable):unavailable(request??{})});
    });
    if(browserName==='firefox')context.on('page',guardFirefoxPage);
    return context;
  };
  try{await use(browser)}finally{browser.newContext=create}
},{scope:'worker'}]});
