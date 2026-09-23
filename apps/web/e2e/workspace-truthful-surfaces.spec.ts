import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};
const workspaces=[
  {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
  {id:"w-beta",name:"Beta Desk",role:"Fund",access_role:"ANALYST"},
];

async function baseMocks(page:import("@playwright/test").Page,onWorkspaceCall?:()=>void){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>{
    onWorkspaceCall?.();
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:workspaces})});
  });
}

function workspaceSelector(page:import("@playwright/test").Page){
  return page.getByRole("combobox",{name:"ACTIVE WORKSPACE"});
}

test.describe("truthful workspace foundations",()=>{
  test("dashboard separates static product metadata from authorized workspace activity",async({page})=>{
    let workspaceCalls=0;
    await baseMocks(page,()=>workspaceCalls+=1);
    await page.route("**/api/v1/history?**",route=>{
      const workspaceId=new URL(route.request().url()).searchParams.get("workspace_id");
      const items=workspaceId==="w-alpha"
        ?[{type:"analysis",id:"alpha-analysis",workspace_id:"w-alpha",engine_id:"B2",demo:false,created_at:"2026-09-23T00:00:00Z"}]
        :[{type:"decision",id:"beta-decision",workspace_id:"w-beta",created_at:"2026-09-23T00:01:00Z"}];
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
    });

    await page.goto("/workspace");
    await expect(page.getByRole("heading",{name:"Product metadata"})).toBeVisible();
    await expect(page.getByText("They are not live activity totals for Alpha Desk.")).toBeVisible();
    await expect(page.getByTestId("workspace-dashboard-activity")).toContainText("B2");
    await expect(page.getByTestId("workspace-dashboard-activity")).toContainText("Connected/direct");

    await workspaceSelector(page).selectOption("w-beta");
    await expect(page.getByTestId("workspace-dashboard-activity")).toContainText("decision");
    await expect(page.getByTestId("workspace-dashboard-activity")).not.toContainText("B2");
    await expect(page.getByText("They are not live activity totals for Beta Desk.")).toBeVisible();
    expect(workspaceCalls).toBe(1);
  });

  test("history and saved analyses render supported summaries instead of raw JSON",async({page})=>{
    await baseMocks(page);
    await page.route("**/api/v1/history?**",route=>route.fulfill({
      status:200,contentType:"application/json",headers:corsHeaders,
      body:JSON.stringify({items:[{type:"analysis",id:"analysis-123",workspace_id:"w-alpha",engine_id:"F3",demo:true,created_at:"2026-09-23T00:02:00Z"}]}),
    }));
    await page.route("**/api/v1/saved-analyses?**",route=>route.fulfill({
      status:200,contentType:"application/json",headers:corsHeaders,
      body:JSON.stringify({items:[{id:"saved-1",workspace_id:"w-alpha",analysis_id:"analysis-123",title:"Liquidation review",archived:false,created_at:"2026-09-23T00:03:00Z"}]}),
    }));

    await page.goto("/workspace/history");
    await expect(page.getByRole("columnheader",{name:"Reference"})).toBeVisible();
    await expect(page.getByText("analysis-123")).toBeVisible();
    await expect(page.getByText("F3")).toBeVisible();
    await expect(page.getByText("Demo")).toBeVisible();
    await expect(page.getByText("This table does not imply a lifetime total.")).toBeVisible();

    await page.getByRole("link",{name:"Saved"}).click();
    await expect(page.getByRole("columnheader",{name:"Analysis reference"})).toBeVisible();
    await expect(page.getByText("Liquidation review")).toBeVisible();
    await expect(page.getByText("analysis-123")).toBeVisible();
    await expect(page.getByText("Active",{exact:true})).toBeVisible();
    await expect(page.locator("pre.result")).toHaveCount(0);
  });

  test("settings shows membership roles and reports organization creation without implying member administration",async({page})=>{
    await baseMocks(page);
    await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"settings-csrf"})}));
    let organizationPosts=0;
    await page.route("**/api/v1/organizations",route=>{
      if(route.request().method()==="POST"){
        organizationPosts+=1;
        return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"org-new",name:"New Research Org",member_role:"OWNER",created_at:"2026-09-23T00:04:00Z"})});
      }
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"org-1",name:"Existing Org",member_role:"ANALYST",created_at:"2026-09-22T00:00:00Z"}]})});
    });

    await page.goto("/workspace/settings");
    await expect(page.getByText("Existing Org")).toBeVisible();
    await expect(page.getByText("ANALYST",{exact:true})).toBeVisible();
    await expect(page.getByText("Member administration is not exposed on this page.")).toBeVisible();
    await expect(page.locator("pre.result")).toHaveCount(0);

    await page.getByLabel("Organization name").fill("New Research Org");
    await page.getByRole("button",{name:"Create organization"}).click();
    await expect(page.getByRole("status")).toContainText("Created New Research Org. Your membership role is OWNER.");
    expect(organizationPosts).toBe(1);
  });
});
