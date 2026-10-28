import {expect,test} from './browser-test';

const authRoutes=[
  "/login",
  "/signup",
  "/forgot-password",
  "/verify-email",
  "/reset-password",
];

test.describe("public production regressions",()=>{
  test('legacy app entry redirects to the existing canonical workspace without forwarding query inputs',async({request})=>{
    const response=await request.get('/app?view=transactions',{maxRedirects:0});
    expect(response.status()).toBe(307);expect(response.headers().location).toBe('/workspace');
  });
  test("genuine healthy service evidence clears its availability warning",async({page})=>{
    test.setTimeout(45000);
    const [response]=await Promise.all([
      page.waitForResponse(async response=>{
        if(new URL(response.url()).pathname!=="/health"||!response.ok())return false;
        try{const body=await response.json();return typeof body?.status==="string"&&["ok","healthy","ready"].includes(body.status.toLowerCase());}catch{return false;}
      },{timeout:35000}),
      page.goto("/",{waitUntil:'domcontentloaded'}),
    ]);
    expect(response.ok()).toBe(true);
    await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA!);
    await expect(page.getByTestId('service-availability')).toHaveCount(0);
  });

  test("auth and recovery forms never submit credentials or tokens with GET",async({page})=>{
    for(const path of authRoutes){
      await page.goto(path,{waitUntil:'domcontentloaded'});
      const form=page.locator("form.form").first();
      await expect(form).toBeVisible();
      await expect(form).toHaveAttribute("method",/^post$/i);
    }
  });

  test("public pages do not overflow a 375px viewport",async({page})=>{
    await page.setViewportSize({width:375,height:812});
    for(const path of ["/","/docs"]){
      await page.goto(path,{waitUntil:'domcontentloaded'});
      await page.evaluate(()=>document.fonts?.ready);
      const dimensions=await page.evaluate(()=>({
        viewport:document.documentElement.clientWidth,
        documentWidth:document.documentElement.scrollWidth,
        bodyWidth:document.body.scrollWidth,
      }));
      expect(dimensions.viewport).toBe(375);
      expect(dimensions.documentWidth,`${path} document overflow`).toBeLessThanOrEqual(dimensions.viewport);
      expect(dimensions.bodyWidth,`${path} body overflow`).toBeLessThanOrEqual(dimensions.viewport);
    }
  });
});


test('public landing uses this build document while private account responses remain uncached',async({request})=>{
 const root=await request.get('/');expect(root.status()).toBe(200);expect(root.headers()['x-rivexis-document']).toBe('build');expect(root.headers()['set-cookie']).toBeUndefined();
 const html=await root.text();expect(html).toContain(`name="rivexis-build" content="${process.env.RIVEXIS_EXPECTED_BUILD_SHA}"`);expect(html.endsWith('</html>')).toBe(true);
 const privateResponse=await request.get('/api/v1/account/settings');expect(privateResponse.status()).toBe(401);expect(privateResponse.headers()['cache-control']).toBe('no-store');expect(privateResponse.headers()['x-rivexis-document']).toBeUndefined();
});
