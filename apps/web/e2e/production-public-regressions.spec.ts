import {expect,test} from "@playwright/test";

const authRoutes=[
  "/login",
  "/signup",
  "/forgot-password",
  "/verify-email",
  "/reset-password",
];

test.describe("public production regressions",()=>{
  test("genuine healthy service evidence clears its availability warning",async({page})=>{
    test.setTimeout(45000);
    const [response]=await Promise.all([
      page.waitForResponse(async response=>{
        if(new URL(response.url()).pathname!=="/health"||!response.ok())return false;
        try{const body=await response.json();return typeof body?.status==="string"&&["ok","healthy","ready"].includes(body.status.toLowerCase());}catch{return false;}
      },{timeout:35000}),
      page.goto("/"),
    ]);
    expect(response.ok()).toBe(true);
    await expect(page.locator('meta[name="rivexis-build"]')).toHaveAttribute('content',process.env.RIVEXIS_EXPECTED_BUILD_SHA!);
    await expect(page.getByTestId('service-availability')).toHaveCount(0);
  });

  test("auth and recovery forms never submit credentials or tokens with GET",async({page})=>{
    for(const path of authRoutes){
      await page.goto(path);
      const form=page.locator("form.form").first();
      await expect(form).toBeVisible();
      await expect(form).toHaveAttribute("method",/^post$/i);
    }
  });

  test("public pages do not overflow a 375px viewport",async({page})=>{
    await page.setViewportSize({width:375,height:812});
    for(const path of ["/","/docs"]){
      await page.goto(path);
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
