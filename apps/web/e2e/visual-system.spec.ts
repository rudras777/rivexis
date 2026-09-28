import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

async function healthMock(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
}

test.describe("Rivexis signature visual system",()=>{
  test("public and auth surfaces keep contextual graphics while using architectural controls",async({page})=>{
    await healthMock(page);
    await page.goto("/");
    const publicBrand=page.getByRole("link",{name:"Rivexis home"}).first().locator("img");
    await expect(publicBrand).toHaveAttribute("src","/brand/rivexis-wordmark.png");
    await expect(publicBrand).toHaveAttribute("alt","Rivexis");
    await expect(page.locator('link[rel="icon"]')).toHaveAttribute("href",/rivexis-icon\.png/);
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute("content",/rivexis-icon\.png/);
    const ambient=page.locator(".publicAmbient");
    await expect(ambient).toBeAttached();
    await expect(ambient).toHaveCSS("background-image",/public-signal-field\.svg/);
    await expect(page.getByRole("link",{name:/Create workspace/})).toHaveCSS("border-radius","2px");
    await expect(page.locator(".decisionCard")).toHaveCSS("border-top-right-radius","34px");
    await expect(page.getByLabel("Illustrative decision brief")).toContainText("Proceed only after the two identified controls are resolved.");
    await expect(page.getByLabel("Illustrative decision evidence")).toContainText("Risk index42/100ModerateConfidence91%HighEvidence18Records");
    await expect(page.getByLabel("Illustrative decision brief")).toContainText("EXAMPLE · NOT LIVE DATA");
    await expect(page.locator(".signalStrip")).toHaveCSS("border-top-left-radius","0px");

    const publicGraphic=await page.request.get("/visuals/public-signal-field.svg");
    expect(publicGraphic.ok()).toBeTruthy();
    expect(publicGraphic.headers()["content-type"]).toContain("image/svg+xml");
    const officialWordmark=await page.request.get("/brand/rivexis-wordmark.png");
    expect(officialWordmark.ok()).toBeTruthy();
    expect(officialWordmark.headers()["content-type"]).toContain("image/png");

    await page.goto("/login");
    await expect(page.getByRole("link",{name:"Rivexis home"}).locator("img")).toHaveAttribute("src","/brand/rivexis-lockup.png");
    await expect(page.locator(".formPage")).toHaveCSS("background-image",/auth-orbit\.svg/);
    await expect(page.locator(".formCard")).toHaveCSS("border-top-right-radius","44px");
    await expect(page.getByLabel("Email")).toHaveCSS("border-radius","2px");
    const authGraphic=await page.request.get("/visuals/auth-orbit.svg");
    expect(authGraphic.ok()).toBeTruthy();
  });

  test("authenticated shell keeps evidence graphics and removes generic pill/card treatment",async({page})=>{
    await healthMock(page);
    await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"}]})}));
    await page.route("**/api/v1/history?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[]})}));
    await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"visual-system-csrf"})}));

    await page.goto("/workspace");
    await expect(page.getByRole("link",{name:"Rivexis home"}).locator("img")).toHaveAttribute("src","/brand/rivexis-wordmark.png");
    await expect(page.locator(".workspaceAmbient")).toHaveCSS("content","normal");
    const ambient=page.locator(".workspaceAmbient");
    await expect(ambient).toBeAttached();
    await expect(ambient).toHaveCSS("background-image",/workspace-evidence-field\.svg/);
    await expect(page.getByRole("link",{name:"Overview"})).toHaveCSS("border-radius","0px");
    await expect(page.getByRole("link",{name:/Run analysis/})).toHaveCSS("border-radius","2px");
    await expect(page.locator(".overviewBand")).toHaveCSS("border-top-right-radius","34px");
    await expect(page.locator(".panel").first()).toHaveCSS("border-top-right-radius","0px");

    const workspaceGraphic=await page.request.get("/visuals/workspace-evidence-field.svg");
    expect(workspaceGraphic.ok()).toBeTruthy();
  });
});
