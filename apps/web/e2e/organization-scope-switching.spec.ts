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

test("organization role drafts do not leak between organizations for the same user",async({page})=>{
  await baseMocks(page);
  await page.route("**/api/v1/organizations",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[
    {id:"org-1",name:"Risk Council",member_role:"OWNER",created_at:"2026-09-28T10:00:00Z"},
    {id:"org-2",name:"Treasury Council",member_role:"OWNER",created_at:"2026-09-28T11:00:00Z"},
  ]})}));
  await page.route("**/api/v1/organizations/org-1/members",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"OWNER",items:[{user_id:"u-shared",email:"shared@example.com",role:"ANALYST",created_at:"2026-09-28T10:05:00Z"}]})}));
  await page.route("**/api/v1/organizations/org-2/members",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"OWNER",items:[{user_id:"u-shared",email:"shared@example.com",role:"VIEWER",created_at:"2026-09-28T11:05:00Z"}]})}));

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
