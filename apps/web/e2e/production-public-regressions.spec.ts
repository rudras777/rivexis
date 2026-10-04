import {expect,test} from "@playwright/test";

const authRoutes=[
  "/login",
  "/signup",
  "/forgot-password",
  "/verify-email",
  "/reset-password",
];

test.describe("public production regressions",()=>{
  test("auth and recovery forms never submit credentials or tokens with GET",async({page})=>{
    for(const path of authRoutes){
      await page.goto(path);
      const forms=page.locator("form");
      await expect(forms).toHaveCount(1);
      await expect(forms.first()).toHaveAttribute("method",/post/i);
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
