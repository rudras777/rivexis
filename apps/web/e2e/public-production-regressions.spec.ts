import {expect,test} from "@playwright/test";

const titledRoutes:[string,string][]=[
  ["/platform","Platform | Rivexis"],
  ["/blockchain-intelligence","Blockchain Intelligence | Rivexis"],
  ["/crypto-finance","Crypto Finance | Rivexis"],
  ["/defi-risk","DeFi Risk | Rivexis"],
  ["/methodology","Methodology | Rivexis"],
  ["/security","Security | Rivexis"],
  ["/docs","Documentation | Rivexis"],
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

test("public navigation exposes DeFi risk and documentation on desktop and tablet",async({page})=>{
  await page.setViewportSize({width:1280,height:800});
  await page.goto("/");
  const desktop=page.locator("nav.desktopPublicNav");
  await expect(desktop.getByRole("link",{name:"DeFi Risk"})).toBeVisible();
  await expect(desktop.getByRole("link",{name:"Docs"})).toBeVisible();

  await page.setViewportSize({width:820,height:900});
  const mobile=page.locator("details.mobileNav");
  await expect(mobile).toBeVisible();
  await mobile.locator("summary").click();
  await expect(mobile.getByRole("link",{name:"DeFi Risk"})).toBeVisible();
  await expect(mobile.getByRole("link",{name:"Docs"})).toBeVisible();
  const dimensions=await page.evaluate(()=>({clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth}));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
});

test("mobile public home has navigation and no horizontal document overflow",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto("/");
  await expect(page.locator("details.mobileNav")).toBeVisible();
  const dimensions=await page.evaluate(()=>({clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth}));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
});
