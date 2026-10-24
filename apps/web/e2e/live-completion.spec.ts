import {test,expect,type Page} from './browser-test';
import AxeBuilder from '@axe-core/playwright';
import path from 'node:path';
const output=path.resolve('../../../../outputs');
async function capturePortraits(page:Page,mode:'desktop'|'mobile'){
 await expect(page.locator('.productVisual')).toHaveCount(3);
 for(const [index,name] of ['liquidation','gasguard','defense'].entries()){
  const figure=page.locator('.productVisual').nth(index),image=figure.locator('.featureDiagram');
  await image.scrollIntoViewIfNeeded();await expect(image).toHaveJSProperty('complete',true);await expect(image).toHaveJSProperty('naturalWidth',600);
  const box=await image.boundingBox();expect(box!.height).toBeGreaterThan(box!.width);
  for(const card of await figure.locator('.compositionCard').all())expect(await card.evaluate(el=>{const s=getComputedStyle(el);return{background:s.backgroundColor,border:s.borderTopWidth,shadow:s.boxShadow}})).toEqual({background:'rgba(0, 0, 0, 0)',border:'0px',shadow:'none'});
  await figure.screenshot({path:path.join(output,`footerless-live-${mode}-${name}.png`)});
 }
}
test('the existing production URL serves the intended exact build and continuous visual',async({page})=>{
 test.setTimeout(60000);
 await page.goto('/',{waitUntil:'domcontentloaded'});await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA!);await expect(page.locator('.signatureRiskField,.riskAtlas,canvas')).toHaveCount(0);await expect(page.locator('.blockchainBackground')).toHaveCount(1);await expect(page.locator('.heroFolioWrap')).toHaveCount(0);await expect(page.getByRole('slider')).toHaveCount(0);await expect(page.getByRole('button',{name:/Switch to .* mode/})).toHaveCount(0);
 await page.setViewportSize({width:1440,height:900});await page.screenshot({path:path.join(output,'footerless-public-guest-desktop.png')});
 const illustration=page.locator('.thresholdPlate');await expect(illustration.locator('.thresholdHeadline strong')).toHaveText(['1.333','1.066']);await expect(illustration.locator('.healthAxis')).toHaveAttribute('aria-label',/threshold 1.000, baseline 1.333, scenario 1.066/);await expect(illustration).toContainText('Hypothetical inputs; no live oracle or execution evidence');await illustration.screenshot({path:path.join(output,'footerless-public-liquidation-illustration.png')});
 for(const selector of ['.showcaseLayout','.gasLayout','.defenseLayout']){const layout=page.locator(selector),copy=await layout.locator(':scope>div').first().boundingBox(),art=await layout.locator(':scope>.productVisual').boundingBox();const [left,right]=selector==='.gasLayout'?[art!,copy!]:[copy!,art!];expect(left.x+left.width,`${selector} alternating columns`).toBeLessThan(right.x);}
 await expect(page.getByRole('contentinfo').locator('a[href*="github.com"]')).toHaveCount(0);
 await capturePortraits(page,'desktop');
 await page.setViewportSize({width:1440,height:1600});
 for(const name of ['liquidation','gas','defense']){const section=page.locator(`.${name}Showcase`),box=await section.boundingBox();expect(box!.width).toBeGreaterThan(1440*.98);await section.screenshot({path:path.join(output,`footerless-live-desktop-${name}-section.png`)})}
});
test('real guest session status is unauthenticated',async({request})=>{
 const status=await request.get('/api/v1/auth/session-status');expect(await status.json()).toEqual({authenticated:false,email_verified:false});
});
for(const route of ['/workspace','/workspace/scenarios','/workspace/frontier','/workspace/transactions','/workspace/reports','/workspace/settings','/workspace/settings/workspaces'])test(`real guest cannot open ${route}`,async({page})=>{
 await page.goto(route,{waitUntil:'domcontentloaded'});await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toHaveCount(0);
 if(route==='/workspace')await page.screenshot({path:path.join(output,'footerless-public-guest-gate.png')});
});
for(const route of ['/app','/demo'])test(`real guest cannot open educational workflow ${route}`,async({page})=>{
 await page.goto(route,{waitUntil:'domcontentloaded'});
 const canonical=route==='/app';
 if(canonical)await expect(page).toHaveURL(/\/workspace$/);
 await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();
 // The default workspace is deliberately omitted from authHref's query.
 const login=page.getByRole('link',{name:'Log in again',exact:true});
 await expect(login).toHaveAttribute('href',canonical?'/login':'/login?next='+encodeURIComponent(route));
 await login.click();await expect(page).toHaveURL(canonical?/\/login$/:/\/login\?next=%2Fdemo$/);
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Explore a hypothetical sample',exact:true})).toHaveCount(0);
});
for(const route of ['/api/v1/workspaces','/api/v1/defi-reports','/api/v1/account/settings','/api/v1/account/export'])test(`real guest API access is rejected: ${route}`,async({request})=>{
 expect((await request.get(route)).status()).toBe(401);
});
test('deployed mobile themes retain accessible navigation, native motion fallback and no overflow',async({page})=>{
 test.setTimeout(60000);await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});
 for(const theme of ['dark','light']){await page.addInitScript(t=>localStorage.setItem('rivexis_theme',t),theme);await page.goto('/',{waitUntil:'domcontentloaded'});await expect(page.getByRole('link',{name:'Sign up',exact:false}).first()).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([]);expect(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');await page.screenshot({path:path.join(output,`footerless-public-guest-mobile-${theme}.png`)});if(theme==='dark')await capturePortraits(page,'mobile');await page.getByLabel('Menu — open navigation',{exact:true}).click();await expect(page.getByRole('navigation',{name:'Mobile navigation'})).toBeVisible()}
});
test('deployed shared background pauses and respects reduced motion',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 // Wait for the real client session request before a one-shot pointer event.
 // Server-rendered art can be visible before its client effect is mounted.
 const session=page.waitForResponse(r=>r.url().endsWith('/api/v1/auth/session-status')&&r.status()===200);
 await page.goto('/',{waitUntil:'domcontentloaded'});await session;
 await expect(page.locator('.blockchainBackground')).toHaveAttribute('data-moving','true');await expect(page.locator('.publicMotionPreferences')).toHaveCount(0);await expect(page.getByRole('contentinfo').getByRole('button',{name:/background motion/i})).toHaveCount(0);await page.emulateMedia({reducedMotion:'reduce'});await expect(page.locator('.blockchainBackground')).toHaveAttribute('data-moving','false');await expect(page.locator('.backgroundMotionButton')).toHaveCount(0);await expect(page.locator('.precisionPointer')).toBeHidden();
});

test('real guest auth pages render secure forms without submitting any credentials',async({page})=>{
 for(const [route,name] of [['/login','login'],['/signup','signup'],['/verify-email','verification']]){await page.goto(route,{waitUntil:'domcontentloaded'});await expect(page.locator('form.form').first()).toHaveAttribute('method','post');await page.screenshot({path:path.join(output,`footerless-public-auth-${name}.png`)})}
});

test('deployed hashed recovery entry clears its synthetic URL credential without requesting or changing a password',async({page,request})=>{
 expect((await request.get('/reset-password?token_hash=SYNTHETIC_HEADER_PROBE')).headers()['referrer-policy']).toBe('no-referrer');
 let confirms=0;page.on('request',req=>{if(req.url().includes('/api/v1/auth/password-reset/confirm'))confirms++});
 await page.goto('/reset-password?token_hash=SYNTHETIC_READ_ONLY_PROBE&type=recovery',{waitUntil:'domcontentloaded'});
 await expect(page).toHaveURL(/\/reset-password\?type=recovery$/);
 await expect(page.getByRole('heading',{name:'Choose a new password',exact:true})).toBeVisible();
 await expect(page.getByLabel('Recovery token')).toHaveCount(0);await expect(page.getByLabel('Email',{exact:true})).toHaveCount(0);
 await expect(page.getByLabel('New password',{exact:true})).toHaveValue('');await expect(page.getByRole('button',{name:'Update password'})).toBeEnabled();
 expect(await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}))).not.toContain('SYNTHETIC_READ_ONLY_PROBE');expect(confirms).toBe(0);
 await page.screenshot({path:path.join(output,'footerless-public-recovery-handoff.png')});
});

test('deployed confirmation entry scrubs synthetic credentials and requires real login',async({page,request})=>{
 expect((await request.get('/login')).headers()['referrer-policy']).toBe('no-referrer');
 let authPosts=0;page.on('request',req=>{if(req.method()==='POST'&&req.url().includes('/api/v1/auth/'))authPosts++});
 await page.goto('/login?verified=1#access_token=SYNTHETIC_CONFIRM_ACCESS&refresh_token=SYNTHETIC_CONFIRM_REFRESH&type=signup',{waitUntil:'domcontentloaded'});
 await expect(page).toHaveURL(/\/login\?verified=1$/);await expect(page.getByRole('status')).toHaveText('Log in to continue after verifying your email.');
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeVisible();
 expect(await (await request.get('/api/v1/auth/session-status')).json()).toEqual({authenticated:false,email_verified:false});expect(authPosts).toBe(0);
 expect(await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}))).not.toContain('SYNTHETIC_CONFIRM');
 await page.screenshot({path:path.join(output,'footerless-public-confirmation-entry.png')});
});
