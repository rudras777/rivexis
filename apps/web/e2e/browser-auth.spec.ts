import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

async function mockHealthyService(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({
    status:200,
    contentType:"application/json",
    headers:corsHeaders,
    body:JSON.stringify({status:"ready"}),
  }));
}

test.describe("browser authentication and onboarding",()=>{
  test("login hides backend identity detail and does not persist bearer tokens",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/auth/web/login",route=>route.fulfill({
      status:401,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({detail:"Account alice@example.com exists but password is wrong"}),
    }));

    await page.goto("/login");
    await page.getByLabel("Email").fill("alice@example.com");
    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button",{name:"Log in"}).click();

    const alert=page.locator(".formCard .error[role='alert']");
    await expect(alert).toHaveText("Invalid email or password.");
    await expect(alert).not.toContainText("alice@example.com");
    await expect(page.getByRole("link",{name:"Forgot your password?"})).toHaveAttribute("href","/forgot-password");

    const storage=await page.evaluate(()=>Object.fromEntries(Object.entries(localStorage)));
    expect(storage).not.toHaveProperty("rivexis_token");
  });

  test("signup conflict stays generic and submit is locked while pending",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/auth/web/signup",async route=>{
      await new Promise(resolve=>setTimeout(resolve,350));
      await route.fulfill({
        status:409,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({detail:"Email already registered"}),
      });
    });

    await page.goto("/signup");
    await page.getByLabel("Email").fill("existing@example.com");
    await page.getByLabel("Password").fill("correct-horse-battery");
    await page.getByRole("button",{name:"Continue"}).click();

    const pending=page.getByRole("button",{name:"Creating account…"});
    await expect(pending).toBeDisabled();

    const alert=page.locator(".formCard .error[role='alert']");
    await expect(alert).toHaveText("Unable to create account with those details.");
    await expect(alert).not.toContainText("already registered");
    await expect(page.getByText(/We verify new accounts/)).toBeVisible();
  });

  test("verification-required signup does not create a browser session",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/auth/web/signup",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({verification_required:true,email_status:"accepted",user:{id:"u1",email:"new@example.com",role:"Individual"}}),
    }));

    await page.goto("/signup");
    await page.getByLabel("Email").fill("new@example.com");
    await page.getByLabel("Password").fill("correct-horse-battery");
    await page.getByRole("button",{name:"Continue"}).click();

    await expect(page).toHaveURL(/\/verify-email\?sent=1$/);
    await expect(page.getByLabel("Email")).toHaveValue("new@example.com");
    expect(await page.evaluate(()=>sessionStorage.getItem("rivexis_pending_verification_email"))).toBe("new@example.com");
  });

  test("password reset request remains enumeration safe",async({page})=>{
    await mockHealthyService(page);
    let csrfCalls=0;
    await page.route("**/api/v1/auth/web/csrf",route=>{csrfCalls+=1;return route.fulfill({status:500,body:"unexpected"});});
    await page.route("**/api/v1/auth/password-reset/request",route=>route.fulfill({
      status:202,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({status:"accepted"}),
    }));

    await page.goto("/forgot-password");
    await page.getByLabel("Email").fill("unknown@example.com");
    await page.getByRole("button",{name:"Send reset link"}).click();

    await expect(page.getByRole("status")).toContainText("If an eligible account exists");
    expect(csrfCalls).toBe(0);
  });

  test("expired recovery token returns a safe actionable error",async({page})=>{
    await mockHealthyService(page);
    await page.route("**/api/v1/auth/password-reset/confirm",route=>route.fulfill({
      status:400,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({detail:"internal token digest mismatch"}),
    }));

    await page.goto("/reset-password?token=expired-token");
    await expect(page.getByLabel("Recovery token")).toHaveValue("expired-token");
    await page.getByLabel("New password",{exact:true}).fill("new-correct-horse");
    await page.getByLabel("Confirm new password").fill("new-correct-horse");
    await page.getByRole("button",{name:"Update password"}).click();

    const alert=page.locator(".formCard .error[role='alert']");
    await expect(alert).toHaveText("This recovery link is invalid or expired. Request a new one.");
    await expect(alert).not.toContainText("digest");
  });

  test("onboarding resumes an existing workspace instead of creating a duplicate",async({page})=>{
    await mockHealthyService(page);
    const workspace={id:"w-existing",name:"Primary Workspace",role:"Individual",access_role:"OWNER"};
    let posts=0;

    await page.route("**/api/v1/workspaces",route=>{
      if(route.request().method()==="POST"){
        posts+=1;
        return route.fulfill({
          status:500,
          contentType:"application/json",
          headers:corsHeaders,
          body:JSON.stringify({detail:"unexpected duplicate create"}),
        });
      }
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({items:[workspace]}),
      });
    });

    await page.goto("/onboarding");
    await expect(page).toHaveURL(/\/workspace$/);
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    expect(posts).toBe(0);
  });

  test("onboarding recovers CSRF after reload and reconciles an ambiguous create",async({page})=>{
    await mockHealthyService(page);
    const workspace={id:"w-created",name:"Primary Workspace",role:"Individual",access_role:"OWNER"};
    let listCalls=0;
    let createCalls=0;
    const csrfHeaders:string[]=[];

    await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({csrf_token:"csrf-recovered"}),
    }));

    await page.route("**/api/v1/me/role",route=>{
      csrfHeaders.push(route.request().headers()["x-rivexis-csrf"]??"");
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({id:"u1",email:"user@example.com",role:"Individual"}),
      });
    });

    await page.route("**/api/v1/workspaces",route=>{
      if(route.request().method()==="POST"){
        createCalls+=1;
        csrfHeaders.push(route.request().headers()["x-rivexis-csrf"]??"");
        return route.fulfill({
          status:503,
          contentType:"application/json",
          headers:corsHeaders,
          body:JSON.stringify({detail:"response interrupted"}),
        });
      }

      listCalls+=1;
      const items=listCalls===1?[]:[workspace];
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({items}),
      });
    });

    await page.goto("/onboarding");
    await expect(page.getByRole("heading",{name:"Configure workspace"})).toBeVisible();
    await page.getByRole("button",{name:"Open workspace"}).click();

    await expect(page).toHaveURL(/\/workspace$/);
    await expect(page.getByRole("navigation",{name:"Workspace"})).toBeVisible();
    expect(createCalls).toBe(1);
    expect(listCalls).toBeGreaterThanOrEqual(2);
    expect(csrfHeaders).toEqual(["csrf-recovered","csrf-recovered"]);

    const selected=await page.evaluate(()=>localStorage.getItem("rivexis_workspace_id"));
    expect(selected).toBe("w-created");
  });
});
