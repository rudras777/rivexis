import {test,expect,type Page,type Route} from '@playwright/test';
const banner=(page:Page)=>page.getByTestId('service-availability');
async function setup(page:Page,respond:(route:Route,number:number)=>unknown){
 await page.clock.install();let requests=0;
 await page.route('**/api/v1/auth/session-status',r=>r.fulfill({json:{authenticated:false,email_verified:false}}));
 await page.route('**/health',r=>respond(r,++requests));
 await page.goto('/',{waitUntil:'domcontentloaded'});return ()=>requests;
}
for(const status of ['ready','healthy','OK'])test(`valid ${status} service status needs no ongoing polling`,async({page})=>{
 const requests=await setup(page,r=>r.fulfill({json:{status}}));await expect.poll(requests).toBe(1);await page.clock.fastForward(120000);await expect(banner(page)).toHaveCount(0);expect(requests()).toBe(1);
});
for(const failure of ['http','transport','json','status'])test(`service warning recovers after transient ${failure} failure`,async({page})=>{
 const requests=await setup(page,(r,n)=>n>1?r.fulfill({json:{status:'ready'}}):failure==='transport'?r.abort('failed'):failure==='json'?r.fulfill({contentType:'application/json',body:'{'}):failure==='status'?r.fulfill({json:{status:42}}):r.fulfill({status:503,json:{detail:'temporarily unavailable'}}));
 await expect(banner(page)).toBeVisible();await page.clock.fastForward(5100);await expect.poll(requests).toBe(2);await expect(banner(page)).toHaveCount(0);await page.clock.fastForward(120000);expect(requests()).toBe(2);
});
test('persistent failure has bounded retries and an explicit recovery control',async({page})=>{
 let healthy=false;const requests=await setup(page,r=>r.fulfill({status:healthy?200:503,json:{status:healthy?'ready':'unavailable'}}));
 await expect(banner(page)).toBeVisible();await page.clock.fastForward(5100);await expect.poll(requests).toBe(2);await expect(banner(page).getByRole('button')).toBeEnabled();await page.clock.fastForward(15100);await expect.poll(requests).toBe(3);await expect(banner(page).getByRole('button')).toBeEnabled();await page.clock.fastForward(300000);expect(requests()).toBe(3);
 healthy=true;await banner(page).getByRole('button',{name:'Retry service status',exact:true}).click();await expect.poll(requests).toBe(4);await expect(banner(page)).toHaveCount(0);
});
test('a stalled health request times out and a bounded retry can recover',async({page})=>{
 const pending:Route[]=[];const requests=await setup(page,(r,n)=>n===1?pending.push(r):r.fulfill({json:{status:'ready'}}));await expect.poll(requests).toBe(1);await page.clock.fastForward(4100);await expect(banner(page)).toBeVisible();await page.clock.fastForward(5100);await expect.poll(requests).toBe(2);await expect(banner(page)).toHaveCount(0);
 await pending[0].fulfill({json:{status:'degraded'}}).catch(()=>{});await expect(banner(page)).toHaveCount(0);
});
test('a hidden tab pauses retries and resumes without parallel requests',async({page})=>{
 const requests=await setup(page,(r,n)=>r.fulfill({status:n===1?503:200,json:{status:n===1?'unavailable':'ready'}}));await expect(banner(page)).toBeVisible();
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'hidden'});document.dispatchEvent(new Event('visibilitychange'))});await page.clock.fastForward(120000);expect(requests()).toBe(1);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'visible'});document.dispatchEvent(new Event('visibilitychange'))});await expect.poll(requests).toBe(2);await expect(banner(page)).toHaveCount(0);
});
test('offline entry does not spend health requests and online recovery is explicit evidence',async({page})=>{
 await page.addInitScript(()=>Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>false}));const requests=await setup(page,r=>r.fulfill({json:{status:'ready'}}));await expect(banner(page)).toBeVisible();await page.clock.fastForward(60000);expect(requests()).toBe(0);
 await page.evaluate(()=>{Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>true});window.dispatchEvent(new Event('online'))});await expect.poll(requests).toBe(1);await expect(banner(page)).toHaveCount(0);
});
test('hidden cancellation ignores an older healthy reply after a newer degraded observation',async({page})=>{
 const pending:Route[]=[];const requests=await setup(page,(r,n)=>n===1?pending.push(r):r.fulfill({json:{status:'degraded'}}));await expect.poll(requests).toBe(1);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'hidden'});document.dispatchEvent(new Event('visibilitychange'))});await page.clock.fastForward(60000);
 await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=> 'visible'});document.dispatchEvent(new Event('visibilitychange'))});await expect.poll(requests).toBe(2);await expect(banner(page)).toContainText('Service availability');await pending[0].fulfill({json:{status:'ready'}}).catch(()=>{});await expect(banner(page)).toContainText('Service availability');
});
test('a real degraded legacy-runtime response retains its security disclosure',async({page})=>{
 const requests=await setup(page,r=>r.fulfill({json:{status:'degraded',reason:'FastAPI runtime unavailable on the approved free-tier stack'}}));await expect(banner(page)).toContainText('authenticated workspace actions and live analyses are unavailable');await page.clock.fastForward(5100);await expect.poll(requests).toBe(2);await expect(banner(page)).toBeVisible();
});
test('online and visibility events do not keep polling a confirmed healthy service',async({page})=>{
 const requests=await setup(page,r=>r.fulfill({json:{status:'ready'}}));await expect.poll(requests).toBe(1);await page.evaluate(()=>{window.dispatchEvent(new Event('online'));document.dispatchEvent(new Event('visibilitychange'))});await page.clock.fastForward(120000);expect(requests()).toBe(1);await expect(banner(page)).toHaveCount(0);
});
test('explicit retry remains disabled while its health request is in flight',async({page})=>{
 const pending:Route[]=[];const requests=await setup(page,(r,n)=>n===1?r.fulfill({status:503}):pending.push(r));await expect(banner(page)).toBeVisible();const retry=banner(page).getByRole('button',{name:'Retry service status',exact:true});await retry.click();await expect.poll(requests).toBe(2);await expect(banner(page).getByRole('button')).toBeDisabled();await pending[0].fulfill({json:{status:'ready'}});await expect(banner(page)).toHaveCount(0);
});
