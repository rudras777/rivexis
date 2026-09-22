import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

const workspace={id:"w-session",name:"Session Workspace",role:"Analyst",access_role:"OWNER"};

async function mockHealthyService(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({
    status:200,
    contentType:"application/json",
    headers:corsHeaders,
    body:JSON.stringify({status:"ready"}),
  }));
}

async function addOpaqueSession(page:import("@playwright/test").Page){
  await page.context().addCookies([{
    name:"rivexis_session",
    value:"opaque-cookie-session",
    url:"http://localhost:8000",
    httpOnly:true,
    sameSite:"Lax",
  }]);
}

test.describe("browser session lifecycle",()=>{
  test("restores a cookie session after reload and logs out with recovered CSRF",async({page})=>{
    await mockHealthyService(page);
    await addOpaqueSession(page);

    let loggedOut=false;
    let workspaceCalls=0;
    let logoutCalls=0;
    const workspaceCookies:string[]=[];
    const csrfCookies:string[]=[];
    const logoutCsrf:string[]=[];

    await page.route("**/api/v1/workspaces",route=>{
      workspaceCalls+=1;
      workspaceCookies.push(route.request().headers()["cookie"]??"");
      if(loggedOut){
        return route.fulfill({
          status:401,
          contentType:"application/json",
          headers:corsHeaders,
          body:JSON.stringify({detail:"revoked server session"}),
        });
      }
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({items:[workspace]}),
      });
    });

    await page.route("**/api/v1/auth/web/csrf",route=>{
      csrfCookies.push(route.request().headers()["cookie"]??"");
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({csrf_token:"csrf-after-reload"}),
      });
    });

    await page.route("**/api/v1/auth/logout",async route=>{
      logoutCalls+=1;
      logoutCsrf.push(route.request().headers()["x-rivexis-csrf"]??"");
      await new Promise(resolve=>setTimeout(resolve,300));
      loggedOut=true;
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({status:"revoked",scope:"all_current_sessions_for_user"}),
      });
    });

    await page.goto("/workspace");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    await expect.poll(()=>workspaceCalls).toBeGreaterThanOrEqual(1);

    await page.reload();
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    await expect.poll(()=>workspaceCalls).toBeGreaterThanOrEqual(2);
    expect(workspaceCookies.every(value=>value.includes("rivexis_session=opaque-cookie-session"))).toBe(true);

    const storageBefore=await page.evaluate(()=>Object.fromEntries(Object.entries(localStorage)));
    expect(storageBefore.rivexis_workspace_id).toBe("w-session");
    expect(storageBefore).not.toHaveProperty("rivexis_token");

    await page.getByRole("button",{name:"Log out"}).click();
    await expect(page.getByRole("button",{name:"Logging out…"})).toBeDisabled();
    await expect(page).toHaveURL(/\/login$/);

    expect(logoutCalls).toBe(1);
    expect(csrfCookies).toHaveLength(1);
    expect(csrfCookies[0]).toContain("rivexis_session=opaque-cookie-session");
    expect(logoutCsrf).toEqual(["csrf-after-reload"]);

    const storageAfter=await page.evaluate(()=>Object.fromEntries(Object.entries(localStorage)));
    expect(storageAfter).not.toHaveProperty("rivexis_workspace_id");
    expect(storageAfter).not.toHaveProperty("rivexis_token");

    await page.goto("/workspace");
    await expect(page.getByTestId("workspace-shell-session")).toContainText("Session ended");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toHaveCount(0);
  });

  test("treats a revoked session during CSRF bootstrap as already logged out",async({page})=>{
    await mockHealthyService(page);
    await addOpaqueSession(page);

    let logoutCalls=0;
    await page.route("**/api/v1/workspaces",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({items:[workspace]}),
    }));
    await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({
      status:401,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({detail:"revoked-session-internal-detail"}),
    }));
    await page.route("**/api/v1/auth/logout",route=>{
      logoutCalls+=1;
      return route.fulfill({status:500,contentType:"application/json",headers:corsHeaders,body:"{}"});
    });

    await page.goto("/workspace");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    await page.evaluate(()=>localStorage.setItem("rivexis_workspace_id","w-stale"));

    await page.getByRole("button",{name:"Log out"}).click();
    await expect(page).toHaveURL(/\/login$/);
    expect(logoutCalls).toBe(0);
    expect(await page.evaluate(()=>localStorage.getItem("rivexis_workspace_id"))).toBeNull();
    await expect(page.getByText("revoked-session-internal-detail")).toHaveCount(0);
  });

  test("keeps local state when logout cannot be confirmed and exposes a safe retry error",async({page})=>{
    await mockHealthyService(page);
    await addOpaqueSession(page);

    let logoutCalls=0;
    await page.route("**/api/v1/workspaces",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({items:[workspace]}),
    }));
    await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({csrf_token:"csrf-for-retry"}),
    }));
    await page.route("**/api/v1/auth/logout",route=>{
      logoutCalls+=1;
      return route.fulfill({
        status:503,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({detail:"redis://secret@internal/session-backend"}),
      });
    });

    await page.goto("/workspace");
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    await page.getByRole("button",{name:"Log out"}).click();

    const alert=page.locator(".sideFoot [role='alert']");
    await expect(alert).toHaveText("Rivexis could not confirm logout. Retry before leaving this device.");
    await expect(alert).not.toContainText("redis://");
    await expect(page).toHaveURL(/\/workspace$/);
    expect(logoutCalls).toBe(1);
    expect(await page.evaluate(()=>localStorage.getItem("rivexis_workspace_id"))).toBe("w-session");
    await expect(page.getByRole("button",{name:"Log out"})).toBeEnabled();
  });
});
