import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

async function baseMocks(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({
    status:200,contentType:"application/json",headers:corsHeaders,
    body:JSON.stringify({items:[{id:"w1",name:"Research Desk",role:"Analyst",access_role:"OWNER"}]}),
  }));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"engine-provenance-csrf"})}));
}

function baseResult(overrides:Record<string,unknown>={}){
  return {
    engine_id:"B1",
    engine_version:"2.1.0",
    analysis_framework_version:"1.0.0",
    analysis_id:"analysis-1",
    engine_run_id:"run-1",
    timestamp:"2026-09-23T07:00:00Z",
    block_reference:null,
    status:"COMPLETED",
    risk_score:0,
    data_confidence:0,
    engine_confidence:0,
    severity:"unknown",
    summary:"No provider result was available.",
    metrics:{},signals:[],warnings:[],hard_blockers:[],mitigations:[],safer_alternatives:[],
    evidence:[],provider_consensus:"UNAVAILABLE",provider_conflicts:[],data_freshness:{},
    missing_data:[],provider_status:[],assumptions:[],demo:false,
    ...overrides,
  };
}

test.describe("engine result provenance",()=>{
  test("provider-unavailable result never claims provider-grounded evidence",async({page})=>{
    await baseMocks(page);
    await page.route("**/api/v1/analysis/simulations",route=>route.fulfill({
      status:200,contentType:"application/json",headers:corsHeaders,
      body:JSON.stringify(baseResult({
        status:"PROVIDER_UNAVAILABLE",
        summary:"Simulation provider is unavailable.",
        missing_data:["simulation provider evidence"],
      })),
    }));

    await page.goto("/workspace/engines/B1");
    await page.getByRole("button",{name:/Live provider analysis/}).click();
    await page.getByRole("button",{name:"Run B1"}).click();

    const summary=page.getByTestId("engine-result-summary");
    await expect(summary).toContainText("PROVIDER UNAVAILABLE — NO DECISION-GRADE PROVIDER RESULT");
    await expect(summary).toContainText("Evidence records0");
    await expect(summary).toContainText("Evidence sourcesNone recorded");
    await expect(summary).toContainText("simulation provider evidence");
    await expect(summary).toContainText("Analysis framework1.0.0");
    await expect(page.getByText("Provider-grounded result / explicit degraded state")).toHaveCount(0);
  });

  test("partial result names only the evidence source actually returned",async({page})=>{
    await baseMocks(page);
    await page.route("**/api/v1/analysis/routes",route=>route.fulfill({
      status:200,contentType:"application/json",headers:corsHeaders,
      body:JSON.stringify(baseResult({
        engine_id:"B5",
        engine_version:"2.4.0",
        analysis_id:"analysis-b5",
        status:"PARTIAL",
        risk_score:32,
        data_confidence:68,
        engine_confidence:72,
        severity:"moderate",
        summary:"Route quote is available but independent security evidence is incomplete.",
        evidence:[{provider:"lifi",source_type:"provider",normalized_value:{route:"quoted"},confidence:80,freshness:"CURRENT"}],
        provider_consensus:"SINGLE_SOURCE",
        missing_data:["independent bridge security assessment"],
      })),
    }));

    await page.goto("/workspace/engines/B5");
    await page.getByRole("button",{name:/Live provider analysis/}).click();
    await page.getByRole("button",{name:"Run B5"}).click();

    const summary=page.getByTestId("engine-result-summary");
    await expect(summary).toContainText("PARTIAL EVIDENCE — ANALYSIS IS INCOMPLETE");
    await expect(summary).toContainText("Evidence records1");
    await expect(summary).toContainText("Evidence sourceslifi");
    await expect(summary).toContainText("Provider consensusSINGLE_SOURCE");
    await expect(summary).toContainText("independent bridge security assessment");
    await expect(summary).not.toContainText("alchemy");
  });
});
