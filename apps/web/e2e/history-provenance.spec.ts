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
  await page.route("**/api/v1/history?**",route=>{
    const workspaceId=new URL(route.request().url()).searchParams.get("workspace_id");
    const items=workspaceId==="w-alpha"?[
      {type:"analysis",id:"analysis-alpha",workspace_id:"w-alpha",engine_id:"B2",demo:false,created_at:"2026-09-23T07:00:00Z"},
      {type:"decision",id:"decision-alpha",workspace_id:"w-alpha",created_at:"2026-09-23T07:01:00Z"},
    ]:[{type:"analysis",id:"analysis-beta",workspace_id:"w-beta",engine_id:"F4",demo:true,created_at:"2026-09-23T07:02:00Z"}];
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
  });
}

test.describe("History canonical provenance",()=>{
  test("loads persisted analysis and decision provenance on demand and clears it on workspace switch",async({page})=>{
    await baseMocks(page);
    let analysisDetailCalls=0;
    let decisionDetailCalls=0;
    await page.route("**/api/v1/analyses/analysis-alpha",route=>{
      analysisDetailCalls+=1;
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
        engine_id:"B2",engine_version:"2.2.0",analysis_framework_version:"1.0.0",analysis_id:"analysis-alpha",
        status:"PARTIAL",risk_score:47,data_confidence:70,engine_confidence:74,severity:"moderate",summary:"Direct state is available; indexed verification is incomplete.",
        demo:false,provider_consensus:"SINGLE_SOURCE",provider_conflicts:[],
        evidence:[{provider:"ethereum_rpc",source_type:"direct_state",confidence:82,freshness:"CURRENT"}],
        missing_data:["indexed approval history"],
      })});
    });
    await page.route("**/api/v1/decisions/decision-alpha",route=>{
      decisionDetailCalls+=1;
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
        decision_id:"decision-alpha",decision:"WAIT",decision_methodology_version:"1.1.0",overall_risk_score:47,
        decision_confidence:58,data_confidence:70,executive_summary:"Evidence remains incomplete.",recommended_action:"Wait.",
        canonical_persistence_verified:true,evidence_count:1,evidence_sources:["ethereum_rpc"],unresolved_conflict_count:0,
        analysis_ids:["analysis-alpha"],engine_versions:{B2:"2.2.0"},engine_statuses:{B2:"PARTIAL"},analysis_framework_versions:{B2:"1.0.0"},
      })});
    });

    await page.goto("/workspace/history");
    const analysisRow=page.getByRole("row").filter({hasText:"analysis-alpha"});
    await analysisRow.getByRole("button",{name:"Inspect"}).click();
    const detail=page.getByTestId("history-provenance-detail");
    await expect(detail).toContainText("Persisted analysis provenance");
    await expect(detail).toContainText("StatusPARTIAL");
    await expect(detail).toContainText("Engine version2.2.0");
    await expect(detail).toContainText("Analysis framework1.0.0");
    await expect(detail).toContainText("Evidence providersethereum_rpc");
    await expect(detail).toContainText("Evidence source typesdirect_state");
    await expect(detail).toContainText("indexed approval history");
    expect(analysisDetailCalls).toBe(1);

    await analysisRow.getByRole("button",{name:"Hide"}).click();
    const decisionRow=page.getByRole("row").filter({hasText:"decision-alpha"});
    await decisionRow.getByRole("button",{name:"Inspect"}).click();
    await expect(detail).toContainText("Persisted decision provenance");
    await expect(detail).toContainText("DecisionWAIT");
    await expect(detail).toContainText("Decision methodology1.1.0");
    await expect(detail).toContainText("Canonical persisted inputsVerified");
    await expect(detail).toContainText("Evidence providersethereum_rpc");
    await expect(detail).toContainText("B2");
    await expect(detail).toContainText("PARTIAL");
    await expect(detail).toContainText("analysis-alpha");
    expect(decisionDetailCalls).toBe(1);

    await page.getByRole("combobox",{name:"ACTIVE WORKSPACE"}).selectOption("w-beta");
    await expect(page.getByText("analysis-beta")).toBeVisible();
    await expect(page.getByTestId("history-provenance-detail")).toHaveCount(0);
    await expect(page.getByText("ethereum_rpc")).toHaveCount(0);
    await expect(page.getByText("analysis-alpha")).toHaveCount(0);
  });
});
