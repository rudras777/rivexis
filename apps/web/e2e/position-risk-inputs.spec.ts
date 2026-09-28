import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("F3 live mode exposes required oracle evidence and sends the canonical position-risk payload",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Risk Desk",role:"Analyst",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"f3-guided-csrf"})}));

  let submitted:Record<string,unknown>|null=null;
  let csrf="";
  await page.route("**/api/v1/analysis/position-risk",route=>{
    submitted=route.request().postDataJSON() as Record<string,unknown>;
    csrf=route.request().headers()["x-rivexis-csrf"]??"";
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
      analysis_id:"analysis-f3",engine_id:"F3",engine_version:"1.3.0",analysis_framework_version:"f3-live-1.3.0",
      status:"UNKNOWN",severity:"unknown",risk_score:null,data_confidence:0,engine_confidence:0,provider_consensus:"UNAVAILABLE",demo:false,
      summary:"No verified live provider evidence is configured.",metrics:{},signals:[],warnings:[],hard_blockers:["NO_VERIFIED_PROVIDER_EVIDENCE"],mitigations:[],safer_alternatives:[],missing_data:["verified live provider evidence"],provider_status:[],provider_conflicts:[],evidence:[],data_freshness:{status:"UNKNOWN"},assumptions:[],created_at:"2026-09-28T13:00:00Z",
    })});
  });

  await page.goto("/workspace/engines/F3");
  await page.getByRole("button",{name:/Live provider analysis/}).click();

  const runButton=page.getByRole("button",{name:"Run F3 analysis"});
  await expect(page.getByText(/Complete required live evidence inputs: Collateral oracle feed/)).toBeVisible();
  await expect(runButton).toBeDisabled();

  const collateralFeed="0x1111111111111111111111111111111111111111";
  const debtFeed="0x2222222222222222222222222222222222222222";
  await page.getByRole("textbox",{name:/^Collateral oracle feed/}).fill(collateralFeed);
  await expect(runButton).toBeEnabled();
  await page.getByLabel("Collateral units").fill("2.5");
  await page.getByLabel("Debt units").fill("2100");
  await page.getByLabel("Liquidation threshold").fill("1.2");
  await page.getByRole("textbox",{name:/^Debt oracle feed/}).fill(debtFeed);
  await page.getByLabel("Debt price USD fallback").fill("1.01");
  await page.getByLabel("Collateral CoinGecko ID").fill("ethereum");
  await page.getByLabel("Price conflict tolerance").fill("2.5");
  await page.getByRole("button",{name:"Run F3 analysis"}).click();

  await expect(page.getByTestId("engine-result-summary")).toContainText("UNKNOWN — NO PROVIDER EVIDENCE RECORDED");
  expect(csrf).toBe("f3-guided-csrf");
  expect(submitted).toMatchObject({
    demo:false,
    workspace_id:"w1",
    input:{
      chain:"ethereum",
      collateral_price_feed:collateralFeed,
      debt_price_feed:debtFeed,
      collateral_units:2.5,
      debt_units:2100,
      debt_price_usd:1.01,
      liquidation_threshold:1.2,
      collateral_coingecko_id:"ethereum",
      price_conflict_tolerance_pct:2.5,
    },
  });
});
