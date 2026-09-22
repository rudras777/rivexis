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

async function mockTwoWorkspaces(page:import("@playwright/test").Page){
  await mockHealthyService(page);
  await page.route("**/api/v1/workspaces",route=>route.fulfill({
    status:200,
    contentType:"application/json",
    headers:corsHeaders,
    body:JSON.stringify({items:[
      {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
      {id:"w-beta",name:"Beta Desk",role:"Analyst",access_role:"ANALYST"},
    ]}),
  }));
}

test.describe("workspace foundations",()=>{
  test("workspace switching never reuses history from the previous workspace",async({page})=>{
    await mockTwoWorkspaces(page);
    const calls:{alpha:number;beta:number}={alpha:0,beta:0};

    await page.route("**/api/v1/history?**",route=>{
      const workspaceId=new URL(route.request().url()).searchParams.get("workspace_id");
      if(workspaceId==="w-alpha")calls.alpha+=1;
      if(workspaceId==="w-beta")calls.beta+=1;
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({items:[{workspace_id:workspaceId,label:workspaceId==="w-alpha"?"Alpha-only history":"Beta-only history"}]}),
      });
    });

    await page.goto("/workspace/history");
    await expect(page.getByTestId("workspace-history-state")).toContainText("Alpha-only history");
    await expect(page.getByRole("combobox",{name:"ACTIVE WORKSPACE"})).toHaveValue("w-alpha");

    await page.getByRole("combobox",{name:"ACTIVE WORKSPACE"}).selectOption("w-beta");
    await expect(page.getByRole("combobox",{name:"ACTIVE WORKSPACE"})).toHaveValue("w-beta");
    await expect(page.getByTestId("workspace-history-state")).toContainText("Beta-only history");
    await expect(page.getByText("Alpha-only history")).toHaveCount(0);
    expect(await page.evaluate(()=>localStorage.getItem("rivexis_workspace_id"))).toBe("w-beta");

    await page.getByRole("combobox",{name:"ACTIVE WORKSPACE"}).selectOption("w-alpha");
    await expect(page.getByTestId("workspace-history-state")).toContainText("Alpha-only history");
    await expect(page.getByText("Beta-only history")).toHaveCount(0);
    expect(calls.alpha).toBeGreaterThanOrEqual(2);
    expect(calls.beta).toBeGreaterThanOrEqual(1);
  });

  test("provider runtime telemetry follows the active workspace while registry health stays global",async({page})=>{
    await mockTwoWorkspaces(page);

    await page.route("**/api/v1/providers/status?**",route=>route.fulfill({
      status:200,
      contentType:"application/json",
      headers:corsHeaders,
      body:JSON.stringify({chain:"ethereum",providers:[{provider_id:"shared-registry-provider",status:"UNCONFIGURED",configured:false}]}),
    }));

    await page.route("**/api/v1/providers/runtime?**",route=>{
      const workspaceId=new URL(route.request().url()).searchParams.get("workspace_id");
      const providers=workspaceId==="w-alpha"?{
        "alpha-runtime-provider":{logical_calls:3,attempts:3,successes:3,failures:0,cache_hits:0,circuit:{state:"CLOSED"}},
      }:{};
      return route.fulfill({
        status:200,
        contentType:"application/json",
        headers:corsHeaders,
        body:JSON.stringify({scope:workspaceId,control_backend:"memory",providers}),
      });
    });

    await page.goto("/workspace/providers");
    await expect(page.getByText("shared-registry-provider")).toBeVisible();
    await expect(page.getByTestId("workspace-provider-runtime")).toContainText("alpha-runtime-provider");

    await page.getByRole("combobox",{name:"ACTIVE WORKSPACE"}).selectOption("w-beta");
    await expect(page.getByText("shared-registry-provider")).toBeVisible();
    await expect(page.getByTestId("workspace-provider-runtime")).toContainText("No provider runtime activity is recorded in this workspace yet.");
    await expect(page.getByText("alpha-runtime-provider")).toHaveCount(0);
  });
});
