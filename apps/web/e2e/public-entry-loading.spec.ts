import {test,expect} from '@playwright/test';

// No response interception: this also runs against the real public deployment.
// Auth pages are loaded only when chosen; no credentials are entered or submitted.
for(const destination of ['login','signup'])test(`public landing defers auth-route work until the ${destination} entry is chosen`,async({page})=>{
 const premature:string[]=[];
 page.on('request',request=>{
  const url=new URL(request.url());
  if(['/login','/signup'].includes(url.pathname)&&!request.isNavigationRequest())premature.push(url.pathname);
 });
 const sessionReady=page.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/api/v1/auth/session-status'),{timeout:15000});
 await page.goto('/',{waitUntil:'domcontentloaded'});await expect(page.locator('#hero-title')).toBeVisible();await sessionReady;
 if(process.env.RIVEXIS_EXPECTED_BUILD_SHA)await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA);
 // Observe a bounded post-hydration window. Unrelated streaming route prefetches
 // need not become globally idle for this specific negative-request assertion.
 await page.waitForTimeout(1000);
 expect(premature,'Do not fetch authentication routes before user intent').toEqual([]);
 const hero=page.locator('.folioHero');
 await hero.getByRole('link',{name:destination==='login'?'Log in':/^Create account/}).click();
 // The default workspace destination intentionally omits a redundant next query.
 await expect(page).toHaveURL(new RegExp(`/${destination}$`));
 await expect(page.getByLabel('Email',{exact:true})).toBeVisible();
});
