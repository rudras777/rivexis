import {expect,test} from "@playwright/test";

const titledRoutes:[string,string][]=[
  ["/platform","Platform | Rivexis"],
  ["/blockchain-intelligence","Blockchain Intelligence | Rivexis"],
  ["/crypto-finance","Crypto Finance | Rivexis"],
  ["/defi-risk","DeFi Risk | Rivexis"],
  ["/methodology","Methodology | Rivexis"],
  ["/security","Security | Rivexis"],
  ["/login","Sign In | Rivexis"],
  ["/signup","Create Workspace | Rivexis"],
  ["/forgot-password","Reset Password | Rivexis"],
  ["/verify-email","Verify Email | Rivexis"],
];

const postFallbackRoutes=["/login","/signup","/forgot-password","/verify-email"];

test("public routes expose route-specific document titles",async({page})=>{
  for(const [route,title] of titledRoutes){
    await page.goto(route);
    await expect(page).toHaveTitle(title);
  }
});

test("auth forms retain POST as their native fallback",async({page})=>{
  for(const route of postFallbackRoutes){
    await page.goto(route);
    const form=page.locator("form").first();
    await expect(form).toHaveAttribute("method",/^post$/i);
  }
});

test("mobile public home has navigation and no horizontal document overflow",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto("/");
  await expect(page.locator("details.mobileNav")).toBeVisible();
  const dimensions=await page.evaluate(()=>({clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth}));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
});
