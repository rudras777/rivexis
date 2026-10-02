import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

async function baseMocks(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Institutional Desk",role:"Fund",organization_id:"org-1",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"org-scope-csrf"})}));
}

async function organizationMocks(page:import("@playwright/test").Page){
  await page.route("**/api/v1/organizations",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[
    {id:"org-1",name:"Risk Council",member_role:"OWNER",created_at:"2026-09-28T10:00:00Z"},
    {id:"org-2",name:"Treasury Council",member_role:"OWNER",created_at:"2026-09-28T11:00:00Z"},
  ]})}));
  await page.route("**/api/v1/organizations/org-1/members",async route=>{
    if(route.request().method()==="POST"){
      await route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({user_id:"u-shared",email:"shared@example.com",role:"VIEWER",created_at:"2026-09-28T10:05:00Z"})});
      return;
    }
    await route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"OWNER",items:[{user_id:"u-shared",email:"shared@example.com",role:"ANALYST",created_at:"2026-09-28T10:05:00Z"}]})});
  });
  await page.route("**/api/v1/organizations/org-2/members",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"OWNER",items:[{user_id:"u-shared",email:"shared@example.com",role:"VIEWER",created_at:"2026-09-28T11:05:00Z"}]})}));
}

test("organization role drafts do not leak between organizations for the same user",async({page})=>{
  await baseMocks(page);
  await organizationMocks(page);

  await page.goto("/workspace/settings");
  await expect(page.getByRole("heading",{name:"Risk Council members"})).toBeVisible();
  await expect(page.getByLabel("Role for shared@example.com")).toHaveValue("ANALYST");

  await page.getByRole("button",{name:"Manage"}).click();
  await expect(page.getByRole("heading",{name:"Treasury Council members"})).toBeVisible();
  await expect(page.getByLabel("Role for shared@example.com")).toHaveValue("VIEWER");

  await page.getByRole("button",{name:"Manage"}).click();
  await expect(page.getByRole("heading",{name:"Risk Council members"})).toBeVisible();
  await expect(page.getByLabel("Role for shared@example.com")).toHaveValue("ANALYST");
});

test("completed organization mutation status does not leak after switching organizations",async({page})=>{
  await baseMocks(page);
  await organizationMocks(page);

  await page.goto("/workspace/settings");
  await expect(page.getByRole("heading",{name:"Risk Council members"})).toBeVisible();
  await page.getByLabel("Role for shared@example.com").selectOption("VIEWER");
  await page.getByRole("button",{name:"Update shared@example.com"}).click();
  await expect(page.getByRole("status").filter({hasText:"Updated shared@example.com to VIEWER."})).toBeVisible();

  await page.getByRole("button",{name:"Manage"}).click();
  await expect(page.getByRole("heading",{name:"Treasury Council members"})).toBeVisible();
  await expect(page.getByText("Updated shared@example.com to VIEWER.",{exact:true})).toHaveCount(0);
});

test("membership claim target is frozen while the authenticated claim request is pending",async({page})=>{
  await baseMocks(page);
  await organizationMocks(page);

  let releaseClaim:()=>void=()=>{};
  const claimGate=new Promise<void>(resolve=>{releaseClaim=resolve});
  await page.route("**/api/v1/organizations/org-target/membership-claim",async route=>{
    await claimGate;
    await route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({organization_id:"org-target",claim_token:"claim_abcdefghijklmnopqrstuvwxyz0123456789",expires_in_seconds:900,expires_at:"2026-09-28T12:15:00Z"})});
  });

  await page.goto("/workspace/settings");
  const target=page.getByLabel("Organization ID for membership claim");
  await target.fill("org-target");
  await page.getByRole("button",{name:"Generate claim"}).click();

  await expect(target).toBeDisabled();
  await expect(page.getByRole("button",{name:"Generating…"})).toBeDisabled();

  releaseClaim();
  await expect(page.getByTestId("generated-membership-claim")).toContainText("org-target");
  await expect(target).toBeEnabled();
});
