import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("organization settings administer existing members and preserve claim-only joins",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Institutional Desk",role:"Fund",organization_id:"org-1",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"org-admin-csrf"})}));
  await page.route("**/api/v1/organizations",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"org-1",name:"Risk Council",member_role:"OWNER",created_at:"2026-09-28T10:00:00Z"}]})}));

  let members=[
    {user_id:"u-owner",email:"owner@example.com",role:"OWNER",created_at:"2026-09-28T10:00:00Z"},
    {user_id:"u-analyst",email:"analyst@example.com",role:"ANALYST",created_at:"2026-09-28T10:05:00Z"},
  ];
  let updateRequest:Record<string,unknown>|null=null;
  let updateCsrf="";
  let acceptRequest:Record<string,unknown>|null=null;
  let acceptCsrf="";
  let removedUser="";
  let removeCsrf="";
  let claimCsrf="";

  await page.route("**/api/v1/organizations/org-1/members/claim",async route=>{
    acceptRequest=route.request().postDataJSON() as Record<string,unknown>;
    acceptCsrf=(await route.request().allHeaders())["x-rivexis-csrf"]??"";
    const added={user_id:"u-new",email:"newmember@example.com",role:String(acceptRequest.role),created_at:"2026-09-28T14:00:00Z"};
    members=[...members.filter(member=>member.user_id!==added.user_id),added];
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(added)});
  });

  await page.route("**/api/v1/organizations/org-1/members/*",async route=>{
    if(route.request().method()!=="DELETE")return route.fallback();
    removedUser=decodeURIComponent(new URL(route.request().url()).pathname.split("/").at(-1)??"");
    removeCsrf=(await route.request().allHeaders())["x-rivexis-csrf"]??"";
    members=members.filter(member=>member.user_id!==removedUser);
    return route.fulfill({status:204,headers:corsHeaders,body:""});
  });

  await page.route("**/api/v1/organizations/org-1/members",async route=>{
    if(route.request().method()==="POST"){
      updateRequest=route.request().postDataJSON() as Record<string,unknown>;
      updateCsrf=(await route.request().allHeaders())["x-rivexis-csrf"]??"";
      const existing=members.find(member=>member.email===updateRequest?.email);
      if(!existing)return route.fulfill({status:409,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({detail:"new organization members require an authenticated membership claim"})});
      existing.role=String(updateRequest.role);
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(existing)});
    }
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({member_role:"OWNER",items:members})});
  });

  await page.route("**/api/v1/organizations/org-target/membership-claim",async route=>{
    claimCsrf=(await route.request().allHeaders())["x-rivexis-csrf"]??"";
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({organization_id:"org-target",claim_token:"claim_abcdefghijklmnopqrstuvwxyz1234567890",expires_in_seconds:900,expires_at:"2026-09-28T14:15:00Z"})});
  });

  await page.goto("/workspace/settings");
  await expect(page.getByTestId("organization-member-admin")).toContainText("Risk Council members");
  await expect(page.getByTestId("organization-member-row")).toHaveCount(2);
  await expect(page.getByText("org-1",{exact:true}).first()).toBeVisible();
  await expect(page.getByText(/Do not add a new person by email alone/)).toBeVisible();
  await expect(page.getByRole("button",{name:/add member/i})).toHaveCount(0);

  await page.getByLabel("Role for analyst@example.com").selectOption("VIEWER");
  await page.getByLabel("Update analyst@example.com").click();
  await expect(page.getByText("Updated analyst@example.com to VIEWER.",{exact:true})).toBeVisible();
  expect(updateRequest).toEqual({email:"analyst@example.com",role:"VIEWER"});
  expect(updateCsrf).toBe("org-admin-csrf");

  const claimToken="member_claim_abcdefghijklmnopqrstuvwxyz123456";
  await page.getByLabel("Membership claim token").fill(claimToken);
  await page.getByLabel("Claim role").selectOption("ANALYST");
  await page.getByRole("button",{name:"Accept claim"}).click();
  await expect(page.getByText("Accepted authenticated membership for newmember@example.com as ANALYST.",{exact:true})).toBeVisible();
  await expect(page.getByTestId("organization-member-row")).toHaveCount(3);
  expect(acceptRequest).toEqual({claim_token:claimToken,role:"ANALYST"});
  expect(acceptCsrf).toBe("org-admin-csrf");

  await page.getByLabel("Remove newmember@example.com").click();
  await expect(page.getByLabel("Confirm remove newmember@example.com")).toBeVisible();
  await page.getByLabel("Confirm remove newmember@example.com").click();
  await expect(page.getByText("Organization member removed.",{exact:true})).toBeVisible();
  await expect(page.getByTestId("organization-member-row")).toHaveCount(2);
  expect(removedUser).toBe("u-new");
  expect(removeCsrf).toBe("org-admin-csrf");

  await page.getByLabel("Organization ID for membership claim").fill("org-target");
  await page.getByRole("button",{name:"Generate claim"}).click();
  const generated=page.getByTestId("generated-membership-claim");
  await expect(generated).toContainText("claim_abcdefghijklmnopqrstuvwxyz1234567890");
  await expect(generated).toContainText("Share this token only with the intended organization OWNER or ADMIN");
  expect(claimCsrf).toBe("org-admin-csrf");
});
