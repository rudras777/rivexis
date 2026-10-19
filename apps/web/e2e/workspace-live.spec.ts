import {test,expect} from '@playwright/test';
test('new production routes require a real verified session before exposing controls',async({page})=>{
 for(const route of ['overview','wallets','contracts','networks']){await page.goto('/workspace/'+route,{waitUntil:'domcontentloaded'});await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA!);await expect(page.getByRole('heading',{name:'Session ended',exact:true})).toBeVisible();await expect(page.getByRole('link',{name:'Log in again'})).toHaveAttribute('href','/login?next='+encodeURIComponent('/workspace/'+route));await expect(page.locator('.connectionPanel')).toHaveCount(0);await expect(page.locator('.blockchainBackground')).toHaveCount(1)}
});
test('new production API rejects unauthenticated reads before quota or RPC',async({request})=>{
 for(const endpoint of ['network','wallet','contract','read']){const response=await request.post('/api/v1/on-chain/'+endpoint,{data:{chainId:1,address:'0x'+'1'.repeat(40),...(endpoint==='read'?{data:'0x18160ddd'}:{})}});expect(response.status()).toBe(401);expect(await response.json()).toMatchObject({detail:expect.any(String)});expect(response.headers()['cache-control']).toContain('no-store')}
});
