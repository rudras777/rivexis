import {expect,test} from './browser-test';

const authRoutes=[
  "/login",
  "/signup",
  "/forgot-password",
  "/verify-email",
  "/reset-password",
];

const authDocumentLinks=[
  {name:'login verification',from:'/login',link:'Verify an existing account',to:'/verify-email'},
  {name:'login signup',from:'/login',link:'Create one',to:'/signup'},
  {name:'signup login',from:'/signup',link:'Log in',to:'/login'},
  {name:'verification continue',from:'/verify-email',link:'Continue to login',to:'/login'},
  {name:'verification return',from:'/verify-email',link:'Return to login',to:'/login'},
  {name:'recovery return',from:'/forgot-password',link:'Return to login',to:'/login'},
  {name:'login signup destination',from:'/login?next=%2Fworkspace%2Ffrontier',link:'Create one',to:'/signup?next=%2Fworkspace%2Ffrontier'},
  {name:'signup login destination',from:'/signup?next=%2Fworkspace%2Ffrontier',link:'Log in',to:'/login?next=%2Fworkspace%2Ffrontier'},
  {name:'verification login destination',from:'/verify-email?next=%2Fworkspace%2Ffrontier',link:'Continue to login',to:'/login?next=%2Fworkspace%2Ffrontier'},
  {name:'invalid destination withheld',from:'/login?next=https%3A%2F%2Fevil.example',link:'Create one',to:'/signup'},
];

test.describe("public production regressions",()=>{
  test.beforeEach(async({baseURL,request})=>{
    if(baseURL&&new URL(baseURL).hostname==='127.0.0.1'){
      const response=await request.get('/api/v1/account/settings');
      expect(response.status()).toBe(503);
      expect(await response.json()).toEqual({detail:'External API upstream disabled in local E2E'});
    }
  });
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

  for(const scenario of authDocumentLinks)test(`auth document navigation: ${scenario.name}`,async({page,baseURL})=>{
    const prefetched:string[]=[];
    page.on('request',request=>{
      const url=new URL(request.url());
      if(authRoutes.includes(url.pathname)&&request.headers()['next-router-prefetch']==='1')prefetched.push(url.pathname);
    });
    const initial=await page.goto(scenario.from,{waitUntil:'domcontentloaded'});
    expect(initial?.status()).toBe(200);
    const link=page.getByRole('link',{name:scenario.link,exact:true});
    await expect(link).toHaveAttribute('href',scenario.to);
    await expect(page.locator('form.form').first().getByRole('button').first()).toBeEnabled();
    await link.hover();
    const target=new URL(scenario.to,baseURL);
    const [document]=await Promise.all([
      page.waitForResponse(response=>response.request().isNavigationRequest()&&new URL(response.url()).pathname===target.pathname),
      link.click(),
    ]);
    expect(document.status()).toBe(200);
    await expect(page).toHaveURL(target.href);
    await expect(page.locator('form.form').first()).toHaveAttribute('method',/^post$/i);
    expect(prefetched).toEqual([]);
  });

  test('compiled recovery document and direct assets retain POST-only hydration and private response headers',async({page,request})=>{
    test.setTimeout(45000);
    let expectedHtml:string|undefined;
    for(const path of ['/forgot-password','/_rivexis-public/recovery.html','/_rivexis-public/recovery']){
      const response=await request.get(path);
      expect(response.status(),path).toBe(200);
      expect(response.headers()['cache-control'],path).toBe('no-store');
      expect(response.headers()['referrer-policy'],path).toBe('no-referrer');
      expect(response.headers()['set-cookie'],path).toBeUndefined();
      const html=await response.text();
      expect(html).toContain(`name="rivexis-build" content="${process.env.RIVEXIS_EXPECTED_BUILD_SHA}"`);
      expect(html).toMatch(/<form\b[^>]*\bmethod="post"/i);
      if(expectedHtml===undefined)expectedHtml=html;else expect(html).toBe(expectedHtml);
    }
    const head=await request.head('/forgot-password');
    expect(head.status()).toBe(200);expect(head.headers()['cache-control']).toBe('no-store');expect(await head.text()).toBe('');
    await page.goto('/login',{waitUntil:'domcontentloaded'});
    const [navigation]=await Promise.all([
      page.waitForResponse(response=>response.request().isNavigationRequest()&&new URL(response.url()).pathname==='/forgot-password'),
      page.getByRole('link',{name:'Forgot your password?',exact:true}).click(),
    ]);
    expect(navigation.status()).toBe(200);expect(navigation.headers()['x-rivexis-document']).toBe('build');
    await expect(page.getByRole('heading',{name:'Reset password',exact:true})).toBeVisible();
    await expect(page.getByRole('button',{name:'Send reset link',exact:true})).toBeEnabled();
    await expect(page.locator('form.form')).toHaveAttribute('method','post');
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
 const artifact=await request.head('/_rivexis-public/landing.html');expect(artifact.status()).toBe(200);expect(artifact.headers()['x-frame-options']).toBe('DENY');expect(artifact.headers()['content-security-policy']).toContain("frame-ancestors 'none'");
 const privateResponse=await request.get('/api/v1/account/settings');expect(privateResponse.status()).toBe(401);expect(privateResponse.headers()['cache-control']).toBe('no-store');expect(privateResponse.headers()['x-rivexis-document']).toBeUndefined();
});
