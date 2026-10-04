import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("organization workspace creation is explicitly scoped to the selected writable organization",async({page})=>{
  let posted:Record<string,unknown>|null=null;
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"org-workspace-csrf"})}));
  await page.route("**/api/v1/workspaces",async route=>{
    if(route.request().method()==="POST"){
      posted=route.request().postDataJSON() as Record<string,unknown>;
      await route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"org-w2",name:"Risk Operations",role:"Fund",organization_id:"org-1",access_role:"ANALYST",created_at:"2026-10-04T15:00:00Z"})});
      return;
    }
    await route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Personal",role:"Analyst",organization_id:null,access_role:"OWNER"}]})});
  });
  await page.route("**/api/v1/organizations",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"org-1",name:"Risk Council",member_role:"ANALYST",created_at:"2026-10-04T14:00:00Z"}]})}));
  await page.route("**/api/v1/organizations/org-1/members",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"ANALYST",items:[]})}));

  await page.goto("/workspace/settings");
  await expect(page.getByRole("heading",{name:"Create Risk Council workspace"})).toBeVisible();
  await page.getByLabel("Organization workspace name").fill("Risk Operations");
  await page.getByLabel("Organization workspace context").selectOption("Fund");
  await page.getByRole("button",{name:"Create organization workspace"}).click();

  await expect.poll(()=>posted).not.toBeNull();
  expect(posted).toEqual({name:"Risk Operations",role:"Fund",organization_id:"org-1"});
  await expect(page.getByRole("status")).toContainText("Created Risk Operations inside Risk Council with ANALYST access");
});

test("viewer organization membership cannot create a workspace",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[]})}));
  await page.route("**/api/v1/organizations",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"org-view",name:"Read Only Council",member_role:"VIEWER",created_at:"2026-10-04T14:00:00Z"}]})}));
  await page.route("**/api/v1/organizations/org-view/members",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"VIEWER",items:[]})}));

  await page.goto("/workspace/settings");
  await expect(page.getByRole("button",{name:"Create organization workspace"})).toBeDisabled();
  await expect(page.getByText("VIEWER membership is read-only.",{exact:false})).toBeVisible();
});
