import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

async function mockHealthyService(page: import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({
    status:200,
    contentType:"application/json",
    headers:corsHeaders,
    body:JSON.stringify({status:"ready"}),
  }));
}

async function mockAuthorizedWorkspace(page: import("@playwright/test").Page){
  await mockHealthyService(page);
  await page.route("**/api/v1/workspaces",route=>route.fulfill({
    status:200,
    contentType:"application/json",
    headers:corsHeaders,
    body:JSON.stringify({items:[
      {id:"w1",name:"Primary Treasury",role:"Individual",access_role:"OWNER"},
      {id:"w2",name:"Research",role:"Organization",access_role:"ANALYST"},
    ]}),
  }));
}

test.describe("workspace shell access states",()=>{
  test("withholds workspace navigation while authorization is loading",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/workspaces",async route=>{
      await new Promise(resolve=>setTimeout(resolve,700));
      await route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({items:[{id:"w1",name:"Primary",role:"Individual",access_role:"OWNER"}]}),
      });
    });

    await page.goto("/workspace");
    await expect(page.getByTestId("workspace-shell-loading")).toContainText("Loading workspace access");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toHaveCount(0);
    await expect(page.getByTestId("workspace-shell-loading")).toHaveCount(0);
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
  });

  test("shows an explicit empty state before workspace tools",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/workspaces",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({items:[]}),
    }));

    await page.goto("/workspace");
    const state=page.getByTestId("workspace-shell-empty");
    await expect(state).toContainText("No workspace configured");
    await expect(state.getByRole("link",{name:"Configure workspace"})).toHaveAttribute("href","/onboarding");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toHaveCount(0);
    await expect(page.getByText("Specialist engines")).toHaveCount(0);
  });

  test("distinguishes an expired or revoked session",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/workspaces",route=>route.fulfill({
      status:401,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({detail:"Session has been revoked"}),
    }));

    await page.goto("/workspace");
    const state=page.getByTestId("workspace-shell-session");
    await expect(state).toContainText("Session ended");
    await expect(state).toContainText("Workspace data has not been shown");
    await expect(state.getByRole("link",{name:"Log in again"})).toHaveAttribute("href","/login");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toHaveCount(0);
  });

  test("exposes active navigation state and logical keyboard focus",async({page})=>{
    await mockAuthorizedWorkspace(page);
    await page.goto("/workspace");
    const nav=page.getByRole("navigation",{name:"Workspace"});
    await expect(nav).toBeVisible();

    const overview=nav.getByRole("link",{name:"Overview"});
    await expect(overview).toHaveAttribute("aria-current","page");

    await page.keyboard.press("Tab");
    const skip=page.getByRole("link",{name:"Skip to workspace content"});
    await expect(skip).toBeFocused();

    await page.keyboard.press("Tab");
    await expect(page.getByRole("link",{name:"Rivexis home"})).toBeFocused();

    await page.keyboard.press("Tab");
    const selector=page.getByRole("combobox",{name:"ACTIVE WORKSPACE"});
    await expect(selector).toBeFocused();
    const focusOutline=await selector.evaluate(el=>{
      const style=getComputedStyle(el);
      return {style:style.outlineStyle,width:style.outlineWidth};
    });
    expect(focusOutline.style).not.toBe("none");
    expect(parseFloat(focusOutline.width)).toBeGreaterThan(0);
  });

  test("keeps workspace controls usable on a narrow mobile viewport",async({page})=>{
    await page.setViewportSize({width:390,height:844});
    await mockAuthorizedWorkspace(page);
    await page.goto("/workspace");

    await expect(page.getByRole("combobox",{name:"ACTIVE WORKSPACE"})).toBeVisible();
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    await expect(page.getByRole("button",{name:"Log out"})).toBeVisible();

    for(const name of ["Overview","Workspaces","Providers","Protocol History","Investigations","Monitors","History","Saved"]){
      await expect(page.getByRole("link",{name,exact:true})).toBeVisible();
    }

    const dimensions=await page.evaluate(()=>({
      scrollWidth:document.documentElement.scrollWidth,
      clientWidth:document.documentElement.clientWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
  });

  test("keeps session recovery actions usable on mobile",async({page})=>{
    await page.setViewportSize({width:390,height:844});
    await mockHealthyService(page);
    await page.route("**/api/v1/workspaces",route=>route.fulfill({
      status:401,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({detail:"Authentication required"}),
    }));

    await page.goto("/workspace");
    const state=page.getByTestId("workspace-shell-session");
    await expect(state.getByRole("link",{name:"Log in again"})).toBeVisible();
    await expect(state.getByRole("link",{name:"Public site"})).toBeVisible();

    const dimensions=await page.evaluate(()=>({
      scrollWidth:document.documentElement.scrollWidth,
      clientWidth:document.documentElement.clientWidth,
    }));
    expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
  });

  test("fails closed when the application API is unavailable",async({page})=>{
    await mockHealthyService(page);
    let calls=0;
    await page.route("**/api/v1/workspaces",route=>{
      calls+=1;
      return route.fulfill({
        status:503,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({detail:"backend unavailable"}),
      });
    });

    await page.goto("/workspace");
    const state=page.getByTestId("workspace-shell-unavailable");
    await expect(state).toContainText("Application services unavailable");
    await expect(state).toContainText("withheld authenticated navigation and workspace content");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toHaveCount(0);
    await state.getByRole("button",{name:"Retry"}).click();
    await expect.poll(()=>calls).toBeGreaterThan(1);
  });
});
