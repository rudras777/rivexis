import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};
const workspaces=[
  {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
  {id:"w-beta",name:"Beta Desk",role:"Analyst",access_role:"ANALYST"},
];

async function baseMocks(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:workspaces})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"workspace-dashboard-csrf"})}));
}

function selector(page:import("@playwright/test").Page){return page.getByRole("combobox",{name:"ACTIVE WORKSPACE"})}

function metricCard(page:import("@playwright/test").Page,label:string){return page.getByText(label,{exact:true}).locator("..")}

test.describe("workspace dashboard and settings truthfulness",()=>{
  test("dashboard uses workspace API evidence and marks unavailable data instead of zero",async({page})=>{
    await baseMocks(page);
    await page.route("**/api/v1/history?**",route=>{
      const id=new URL(route.request().url()).searchParams.get("workspace_id");
      if(id==="w-beta")return route.fulfill({status:503,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({detail:"internal history backend unavailable"})});
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[
        {type:"analysis",id:"analysis-alpha",workspace_id:"w-alpha",engine_id:"B2",demo:false,created_at:"2026-09-23T00:00:00Z"},
        {type:"decision",id:"decision-alpha",workspace_id:"w-alpha",created_at:"2026-09-22T23:59:00Z"},
      ]})});
    });
    await page.route("**/api/v1/saved-analyses?**",route=>{
      const id=new URL(route.request().url()).searchParams.get("workspace_id");
      const items=id==="w-alpha"?[{id:"saved-alpha",workspace_id:id,analysis_id:"analysis-alpha",title:"Alpha saved",archived:false,created_at:"2026-09-23T00:00:00Z"}]:[];
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
    });
    await page.route("**/api/v1/monitors?**",route=>{
      const id=new URL(route.request().url()).searchParams.get("workspace_id");
      const items=id==="w-alpha"?[{id:"m1"},{id:"m2"}]:[];
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
    });
    await page.route("**/api/v1/providers/runtime?**",route=>{
      const id=new URL(route.request().url()).searchParams.get("workspace_id");
      const providers=id==="w-alpha"?{rpc:{logical_calls:7}}:{};
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({scope:id,control_backend:"memory",providers})});
    });

    await page.goto("/workspace");
    await expect(metricCard(page,"Recent history records")).toContainText("2");
    await expect(metricCard(page,"Saved analyses")).toContainText("1");
    await expect(metricCard(page,"Configured monitors")).toContainText("2");
    await expect(metricCard(page,"Recorded provider calls")).toContainText("7");
    await expect(page.getByTestId("workspace-recent-activity")).toContainText("analysis-alpha");
    await expect(page.getByText("static product metadata")).toBeVisible();

    await selector(page).selectOption("w-beta");
    await expect(metricCard(page,"Recent history records")).toContainText("Unavailable");
    await expect(metricCard(page,"Saved analyses")).toContainText("0");
    await expect(metricCard(page,"Configured monitors")).toContainText("0");
    await expect(metricCard(page,"Recorded provider calls")).toContainText("0");
    await expect(page.getByTestId("workspace-recent-activity")).toContainText("has not substituted cached or synthetic records");
    await expect(page.getByText("analysis-alpha")).toHaveCount(0);
  });

  test("workspace editing and audit activity are exposed only where management access exists",async({page})=>{
    await baseMocks(page);
    let patchCalls=0;
    let betaAuditCalls=0;
    await page.route("**/api/v1/organizations",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[]})}));
    await page.route("**/api/v1/workspaces/w-alpha/audit-logs?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"audit-1",actor:"owner@example.com",action:"workspace.update",resource_type:"workspace",resource_id:"w-alpha",created_at:"2026-09-23T00:00:00Z"}]})}));
    await page.route("**/api/v1/workspaces/w-beta/audit-logs?**",route=>{betaAuditCalls+=1;return route.fulfill({status:403,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({detail:"should not be requested"})})});
    await page.route("**/api/v1/workspaces/w-alpha",route=>{
      if(route.request().method()!=="PATCH")return route.continue();
      patchCalls+=1;
      const body=route.request().postDataJSON() as {name:string;role:string};
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({...workspaces[0],name:body.name,role:body.role})});
    });

    await page.goto("/workspace/settings");
    await expect(page.getByTestId("workspace-admin-activity")).toContainText("workspace.update");
    await page.getByLabel("Workspace name").fill("Alpha Renamed");
    await page.getByRole("button",{name:"Save workspace changes"}).click();
    await expect.poll(()=>patchCalls).toBe(1);
    await expect(page.getByRole("combobox",{name:"ACTIVE WORKSPACE"})).toContainText("Alpha Renamed");

    await selector(page).selectOption("w-beta");
    await expect(page.getByTestId("active-workspace-settings")).toContainText("requires OWNER or ADMIN access");
    await expect(page.getByTestId("workspace-admin-activity")).toContainText("requires OWNER or ADMIN access");
    await expect(page.getByRole("button",{name:"Save workspace changes"})).toHaveCount(0);
    expect(betaAuditCalls).toBe(0);
  });

  test("saved analyses can be archived and restored without deleting the underlying analysis",async({page})=>{
    await baseMocks(page);
    let archived=false;
    let patchCalls=0;
    await page.route("**/api/v1/saved-analyses?**",route=>{
      const url=new URL(route.request().url());
      const includeArchived=url.searchParams.get("include_archived")==="true";
      const items=archived&&!includeArchived?[]:[{id:"saved-alpha",workspace_id:"w-alpha",analysis_id:"analysis-alpha",title:"Quarterly risk review",archived,created_at:"2026-09-23T00:00:00Z"}];
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
    });
    await page.route("**/api/v1/saved-analyses/saved-alpha?**",route=>{
      patchCalls+=1;
      archived=new URL(route.request().url()).searchParams.get("archived")==="true";
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"saved-alpha",workspace_id:"w-alpha",analysis_id:"analysis-alpha",title:"Quarterly risk review",archived,created_at:"2026-09-23T00:00:00Z"})});
    });

    await page.goto("/workspace/saved");
    await expect(page.getByText("Quarterly risk review")).toBeVisible();
    await page.getByRole("button",{name:"Archive"}).click();
    await expect(page.getByTestId("workspace-saved-state")).toContainText("No active saved analyses exist in this workspace yet.");

    await page.getByLabel("Include archived references").check();
    await expect(page.getByText("Quarterly risk review")).toBeVisible();
    await expect(page.getByTestId("workspace-saved-state")).toContainText("Archived");
    await page.getByRole("button",{name:"Restore"}).click();
    await expect(page.getByTestId("workspace-saved-state")).toContainText("Active");
    expect(patchCalls).toBe(2);
  });
});
