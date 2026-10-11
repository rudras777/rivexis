import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
type Stats={draws:number;deleted:number;contexts:number};
async function prepare(page:Page){
 await page.route('**/health',r=>r.fulfill({status:200,json:{status:'ready'}}));
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({status:200,json:{authenticated:false,email_verified:false}}));
 await page.addInitScript(()=>{
  const stats={draws:0,deleted:0,contexts:0};Object.assign(window,{__atlasStats:stats});
  const original=HTMLCanvasElement.prototype.getContext,seen=new WeakSet();
  HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,...args:unknown[]){const result=Reflect.apply(original,this,args);if(args[0]==='webgl'&&result&&!seen.has(result)){seen.add(result);stats.contexts++;const gl=result as WebGLRenderingContext,draw=gl.drawArrays.bind(gl),remove=gl.deleteBuffer.bind(gl);gl.drawArrays=(mode,first,count)=>{draw(mode,first,count);stats.draws++};gl.deleteBuffer=buffer=>{remove(buffer);stats.deleted++};}return result} as typeof original;
 });
}
const stats=(page:Page)=>page.evaluate(()=>(window as unknown as {__atlasStats:Stats}).__atlasStats);

test('limited CPU, data saving and forced colors do not allocate a graphics scene',async({browser})=>{
 for(const mode of ['cpu','data','colors']){
  const context=await browser.newContext({viewport:{width:1440,height:900}});const page=await context.newPage();await prepare(page);
  if(mode==='cpu')await page.addInitScript(()=>Object.defineProperty(navigator,'hardwareConcurrency',{value:2}));
  if(mode==='data')await page.addInitScript(()=>Object.defineProperty(navigator,'connection',{value:{saveData:true}}));
  if(mode==='colors')await page.emulateMedia({forcedColors:'active'});
  await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-atlas-motion','static');expect((await stats(page)).contexts).toBe(0);
  await page.getByRole('button',{name:'Transaction',exact:true}).click();await expect(page.locator('.atlasVectorPaths circle')).toHaveCount(4);await context.close();
 }
});
test.beforeEach(async({page})=>{await prepare(page)});

test('genuine WebGL draws original geometry without calling financial APIs and pauses on demand',async({page})=>{
 await page.setViewportSize({width:1440,height:900});let financial=0;page.on('request',r=>{if(/\/api\/v1\/defi\//.test(r.url()))financial++});await page.goto('/');
 await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');await expect.poll(async()=>(await stats(page)).draws).toBeGreaterThan(0);
 expect((await stats(page)).contexts).toBe(1);expect(financial).toBe(0);
 await page.screenshot({path:`../../../../outputs/risk-atlas-prototype-${test.info().project.name}-desktop.png`});
 await page.getByRole('button',{name:'Pause motion',exact:true}).click();await expect(page.locator('.atlasEnvironment')).toHaveAttribute('data-motion','paused');
 await page.waitForTimeout(150);const paused=(await stats(page)).draws;await page.waitForTimeout(350);expect((await stats(page)).draws).toBe(paused);
 await page.getByRole('button',{name:'Resume motion',exact:true}).click();await expect.poll(async()=>(await stats(page)).draws).toBeGreaterThan(paused);
});

test('illustrative chapter controls and scroll progression retain readable product evidence',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/');await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');
 for(const [name,text] of [['Boundary','The boundary is conditional'],['Transaction','A proposed action meets'],['Alternatives','Available capital creates']]){await page.getByRole('button',{name,exact:true}).click();await expect(page.locator('.atlasDescription')).toContainText(text);await expect(page.getByRole('button',{name,exact:true})).toHaveAttribute('aria-pressed','true')}
 await page.mouse.wheel(0,100);await page.locator('.gasShowcase').scrollIntoViewIfNeeded();await expect(page.locator('main')).toHaveAttribute('data-atlas-chapter','3');
 await page.locator('.defenseShowcase').scrollIntoViewIfNeeded();await expect(page.locator('main')).toHaveAttribute('data-atlas-chapter','4');
 await expect(page.locator('.defenseComparison')).toContainText('Hypothetical inputs');await expect(page.locator('.thresholdPlate')).toContainText('NOT LIVE DATA');
});

test('reduced motion releases WebGL resources and keeps the vector experience usable',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/');await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');
 await page.emulateMedia({reducedMotion:'reduce'});await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','vector');await expect.poll(async()=>(await stats(page)).deleted).toBe(5);
 await expect(page.getByRole('button',{name:'Static view',exact:true})).toBeDisabled();const count=(await stats(page)).draws;await page.waitForTimeout(350);expect((await stats(page)).draws).toBe(count);
 await page.getByRole('button',{name:'Alternatives',exact:true}).click();await expect(page.locator('.atlasDescription')).toContainText('Available capital creates');
 await expect(page.locator('.atlasVectorPaths path')).toHaveCount(3);
 await page.emulateMedia({reducedMotion:'no-preference'});await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');await expect.poll(async()=>(await stats(page)).draws).toBeGreaterThan(count);
});

test('lost graphics context falls back without removing navigation or account entry',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/');await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');
 await page.locator('.atlasEnvironment').evaluate(canvas=>(canvas as HTMLCanvasElement).getContext('webgl')?.getExtension('WEBGL_lose_context')?.loseContext());
 await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','vector');await expect(page.locator('main')).toHaveAttribute('data-atlas-motion','static');
 await expect(page.getByRole('link',{name:'Create account',exact:true}).first()).toBeVisible();const count=(await stats(page)).draws;await page.waitForTimeout(350);expect((await stats(page)).draws).toBe(count);
});

test('unavailable WebGL preserves an accessible static view',async({page})=>{
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,...args:unknown[]){return args[0]==='webgl'?null:Reflect.apply(original,this,args)} as typeof original;});
 await page.setViewportSize({width:1440,height:900});await page.goto('/');await expect(page.getByRole('button',{name:'Static view',exact:true})).toBeDisabled();await expect(page.locator('main')).toHaveAttribute('data-atlas-motion','static');expect((await stats(page)).draws).toBe(0);
 const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();expect(scan.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([]);
});

test('leaving the landing page disposes the scene and ends rendering',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/');await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');
 await page.locator('.folioNav').getByRole('link',{name:'Log in',exact:true}).click();await expect(page).toHaveURL(/\/login$/);await expect.poll(async()=>(await stats(page)).deleted).toBe(5);const count=(await stats(page)).draws;await page.waitForTimeout(350);expect((await stats(page)).draws).toBe(count);
});

test('touch, tablet and high-density rendering remain bounded with no page overflow',async({browser})=>{
 for(const options of [{viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true},{viewport:{width:768,height:1024},deviceScaleFactor:2},{viewport:{width:1440,height:900},deviceScaleFactor:2}]){
  const context=await browser.newContext(options);const page=await context.newPage();await prepare(page);await page.goto('/');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  if(options.viewport.width<760){await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','vector');expect((await stats(page)).contexts).toBe(0);await page.screenshot({path:`../../../../outputs/risk-atlas-prototype-${test.info().project.name}-mobile.png`,fullPage:true})}else{await expect(page.locator('.riskAtlas')).toHaveAttribute('data-graphics','webgl');expect(await page.locator('.atlasEnvironment').evaluate(e=>(e as HTMLCanvasElement).width)).toBeLessThanOrEqual(2304)}
  await context.close();
 }
});
