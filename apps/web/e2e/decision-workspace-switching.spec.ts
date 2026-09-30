import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("a decision created after a workspace switch remains persisted only in its origin context",async({page})=>{
  const workspaces=[
    {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
    {id:"w-beta",name:"Beta Desk",role:"Analyst",access_role:"OWNER"},
  ];
  let releaseDecision:()=>void=()=>{};
  const decisionGate=new Promise<void>(resolve=>{releaseDecision=resolve});

  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:workspaces})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"decision-switch-csrf"})}));
  await page.route("**/api/v1/history?**",route=>{
    const workspaceId=new URL(route.request().url()).searchParams.get("workspace_id");
    const item=workspaceId==="w-alpha"
      ? {type:"analysis",id:"analysis-alpha",workspace_id:"w-alpha",engine_id:"B2",demo:false,created_at:"2026-09-30T10:00:00Z"}
      : {type:"analysis",id:"analysis-beta",workspace_id:"w-beta",engine_id:"B3",demo:false,created_at:"2026-09-30T11:00:00Z"};
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[item]})});
  });
  await page.route("**/api/v1/analyses/analysis-alpha",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({analysis_id:"analysis-alpha",engine_id:"B2",status:"PARTIAL",workspace_id:"w-alpha"})}));
  await page.route("**/api/v1/decisions/analyze",async route=>{
    await decisionGate;
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({decision_id:"decision-alpha",decision:"WAIT",workspace_id:"w-alpha"})});
  });

  await page.goto("/workspace/decisions");
  await page.getByLabel("Select analysis analysis-alpha for decision").check();
  await page.getByRole("button",{name:/Create canonical decision/}).click();

  await page.getByLabel("ACTIVE WORKSPACE").selectOption("w-beta");
  await expect(page.getByLabel("Select analysis analysis-beta for decision")).toBeVisible();
  await expect(page.getByLabel("Select analysis analysis-alpha for decision")).toHaveCount(0);

  releaseDecision();
  await expect(page.getByText(/Persisted decision decision-alpha created/)).toHaveCount(0);
  await expect(page.getByTestId("decision-report-workbench")).toHaveCount(0);
});
