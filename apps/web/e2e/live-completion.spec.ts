import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import path from 'node:path';
const output=path.resolve('../../../../outputs');
test('the existing production URL serves the intended exact build and continuous visual',async({page})=>{
 await page.goto('/');await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA!);await expect(page.locator('.signatureRiskField')).toBeVisible();await expect(page.locator('.heroFolioWrap')).toHaveCount(0);await expect(page.getByRole('slider')).toHaveCount(0);
 await page.setViewportSize({width:1440,height:900});await page.screenshot({path:path.join(output,'completion-live-guest-desktop.png')});
 const illustration=page.locator('.thresholdPlate');await expect(illustration.locator('.thresholdHeadline strong')).toHaveText(['1.333','1.066']);await expect(illustration.locator('.healthAxis')).toHaveAttribute('aria-label',/threshold 1.000, baseline 1.333, scenario 1.066/);await expect(illustration).toContainText('Hypothetical inputs; no live oracle or execution evidence');await illustration.screenshot({path:path.join(output,'completion-live-liquidation-illustration.png')});
});
test('real guest sessions cannot open any financial workspace or educational workflow',async({page,request})=>{
 const status=await request.get('/api/v1/auth/session-status');expect(await status.json()).toEqual({authenticated:false,email_verified:false});
 for(const route of ['/workspace','/workspace/scenarios','/workspace/frontier','/workspace/transactions','/workspace/reports']){await page.goto(route);await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Inspect wallet',exact:true})).toHaveCount(0)}
 for(const route of ['/app','/demo']){await page.goto(route);await expect(page.getByRole('heading',{name:'Your intelligence workspace',exact:true})).toBeVisible();await expect(page.getByRole('link',{name:'Log in',exact:true})).toHaveAttribute('href','/login?next='+encodeURIComponent(route));await expect(page.getByRole('button',{name:'Explore a hypothetical sample',exact:true})).toHaveCount(0)}
 for(const route of ['/api/v1/workspaces','/api/v1/defi-reports'])expect((await request.get(route)).status()).toBe(401);
 await page.screenshot({path:path.join(output,'completion-live-guest-gate.png')});
});
test('deployed mobile themes retain accessible navigation, native motion fallback and no overflow',async({page})=>{
 test.setTimeout(60000);await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});
 for(const theme of ['dark','light']){await page.addInitScript(t=>localStorage.setItem('rivexis_theme',t),theme);await page.goto('/');await expect(page.getByRole('link',{name:'Sign up',exact:false}).first()).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([]);expect(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior)).toBe('auto');await page.screenshot({path:path.join(output,`completion-live-guest-mobile-${theme}.png`)});await page.getByLabel('Menu — open navigation',{exact:true}).click();await expect(page.getByRole('navigation',{name:'Mobile navigation'})).toBeVisible()}
});
test('deployed depth responds to bounded pointer input and resets on reduced motion',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/');const art=page.locator('.signatureRiskField'),box=(await art.boundingBox())!;await page.mouse.move(box.x+box.width*.8,box.y+box.height*.4);await expect.poll(()=>art.evaluate(e=>e.style.getPropertyValue('--field-x'))).not.toBe('');const angle=await art.evaluate(e=>parseFloat(e.style.getPropertyValue('--field-x')));expect(Math.abs(angle)).toBeLessThanOrEqual(2.5);await page.emulateMedia({reducedMotion:'reduce'});await expect.poll(()=>art.evaluate(e=>e.style.getPropertyValue('--field-x'))).toBe('');await expect(page.locator('.precisionPointer')).toBeHidden();
});

test('real guest auth pages render secure forms without submitting any credentials',async({page})=>{
 for(const [route,name] of [['/login','login'],['/signup','signup'],['/verify-email','verification']]){await page.goto(route);await expect(page.locator('form.form').first()).toHaveAttribute('method','post');await page.screenshot({path:path.join(output,`completion-live-auth-${name}.png`)})}
});

test('deployed hashed recovery entry clears its synthetic URL credential without requesting or changing a password',async({page,request})=>{
 expect((await request.get('/reset-password?token_hash=SYNTHETIC_HEADER_PROBE')).headers()['referrer-policy']).toBe('no-referrer');
 let confirms=0;page.on('request',req=>{if(req.url().includes('/api/v1/auth/password-reset/confirm'))confirms++});
 await page.goto('/reset-password?token_hash=SYNTHETIC_READ_ONLY_PROBE&type=recovery');
 await expect(page).toHaveURL(/\/reset-password\?type=recovery$/);
 await expect(page.getByRole('heading',{name:'Choose a new password',exact:true})).toBeVisible();
 await expect(page.getByLabel('Recovery token')).toHaveCount(0);await expect(page.getByLabel('Email',{exact:true})).toHaveCount(0);
 await expect(page.getByLabel('New password',{exact:true})).toHaveValue('');await expect(page.getByRole('button',{name:'Update password'})).toBeEnabled();
 expect(await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}))).not.toContain('SYNTHETIC_READ_ONLY_PROBE');expect(confirms).toBe(0);
 await page.screenshot({path:path.join(output,'completion-live-recovery-handoff.png')});
});

test('deployed confirmation entry scrubs synthetic credentials and requires real login',async({page,request})=>{
 expect((await request.get('/login')).headers()['referrer-policy']).toBe('no-referrer');
 let authPosts=0;page.on('request',req=>{if(req.method()==='POST'&&req.url().includes('/api/v1/auth/'))authPosts++});
 await page.goto('/login?verified=1#access_token=SYNTHETIC_CONFIRM_ACCESS&refresh_token=SYNTHETIC_CONFIRM_REFRESH&type=signup');
 await expect(page).toHaveURL(/\/login\?verified=1$/);await expect(page.getByRole('status')).toHaveText('Log in to continue after verifying your email.');
 await expect(page.getByRole('button',{name:'Log in',exact:true})).toBeVisible();
 expect(await (await request.get('/api/v1/auth/session-status')).json()).toEqual({authenticated:false,email_verified:false});expect(authPosts).toBe(0);
 expect(await page.evaluate(()=>JSON.stringify({...localStorage,...sessionStorage}))).not.toContain('SYNTHETIC_CONFIRM');
 await page.screenshot({path:path.join(output,'completion-live-confirmation-entry.png')});
});
