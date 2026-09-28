import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("F5 live mode builds canonical treasury allocations without silent normalization",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Treasury Desk",role:"Treasury",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"treasury-builder-csrf"})}));

  let submitted:Record<string,unknown>|null=null;
  let csrf="";
  await page.route("**/api/v1/analysis/treasury",route=>{
    submitted=route.request().postDataJSON() as Record<string,unknown>;
    csrf=route.request().headers()["x-rivexis-csrf"]??"";
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
      analysis_id:"analysis-f5",engine_id:"F5",engine_version:"1.2.0",analysis_framework_version:"f5-live-1.3.0",
      status:"UNKNOWN",severity:"unknown",risk_score:null,data_confidence:0,engine_confidence:0,provider_consensus:"UNAVAILABLE",demo:false,
      summary:"No verified live provider evidence is configured.",metrics:{},signals:[],warnings:[],hard_blockers:["NO_VERIFIED_PROVIDER_EVIDENCE"],mitigations:[],safer_alternatives:[],missing_data:["verified live provider evidence"],provider_status:[],provider_conflicts:[],evidence:[],data_freshness:{status:"UNKNOWN"},assumptions:[],created_at:"2026-09-28T12:00:00Z",
    })});
  });

  await page.goto("/workspace/engines/F5");
  await page.getByRole("button",{name:/Live provider analysis/}).click();

  const builder=page.getByTestId("treasury-allocation-builder");
  await expect(builder).toBeVisible();
  await expect(page.getByTestId("treasury-allocation-row")).toHaveCount(3);
  await expect(builder).toContainText("WEIGHT 100.00%");
  await expect(page.getByLabel("Engine input JSON")).not.toBeVisible();

  await page.getByLabel("Capital").fill("2000000");
  await page.getByLabel("Concentration limit").fill("40");
  await page.getByLabel("Remove allocation 2").click();
  await expect(page.getByTestId("treasury-allocation-row")).toHaveCount(2);
  await expect(builder).toContainText("WEIGHT 75.00%");

  await page.getByRole("button",{name:"Add allocation"}).click();
  await page.getByLabel("Allocation 3 CoinGecko asset ID").fill("chainlink");
  await page.getByLabel("Allocation 3 symbol").fill("LINK");
  await page.getByLabel("Allocation 3 weight").fill("25");
  await expect(page.getByLabel("Allocation 3 stablecoin")).not.toBeChecked();
  await expect(builder).toContainText("WEIGHT 100.00%");

  await page.getByRole("button",{name:"Run F5"}).click();

  expect(csrf).toBe("treasury-builder-csrf");
  expect(submitted).toMatchObject({
    demo:false,
    workspace_id:"w1",
    input:{
      capital_usd:2000000,
      max_concentration_pct:40,
      market_shock_pct:30,
      stablecoin_depeg_pct:10,
      allocations:[
        {coingecko_id:"bitcoin",symbol:"BTC",weight_pct:30,stablecoin:false},
        {coingecko_id:"usd-coin",symbol:"USDC",weight_pct:45,stablecoin:true},
        {coingecko_id:"chainlink",symbol:"LINK",weight_pct:25,stablecoin:false},
      ],
    },
  });
  await expect(page.getByTestId("engine-result-summary")).toContainText("UNKNOWN — NO PROVIDER EVIDENCE RECORDED");
});
