import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("F1 live mode builds canonical manual positions without raw JSON editing",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Research Desk",role:"Analyst",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"portfolio-builder-csrf"})}));

  let submitted:Record<string,unknown>|null=null;
  let csrf="";
  await page.route("**/api/v1/analysis/portfolio",route=>{
    submitted=route.request().postDataJSON() as Record<string,unknown>;
    csrf=route.request().headers()["x-rivexis-csrf"]??"";
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
      analysis_id:"analysis-f1",engine_id:"F1",engine_version:"1.2.0",analysis_framework_version:"f1-live-1.4.0",
      status:"UNKNOWN",severity:"unknown",risk_score:null,data_confidence:0,engine_confidence:0,provider_consensus:"UNAVAILABLE",demo:false,
      summary:"No verified live provider evidence is configured.",metrics:{},signals:[],warnings:[],hard_blockers:["NO_VERIFIED_PROVIDER_EVIDENCE"],mitigations:[],safer_alternatives:[],missing_data:["verified live provider evidence"],provider_status:[],provider_conflicts:[],evidence:[],data_freshness:{status:"UNKNOWN"},assumptions:[],created_at:"2026-09-28T12:00:00Z",
    })});
  });

  await page.goto("/workspace/engines/F1");
  await page.getByRole("button",{name:/Live provider analysis/}).click();

  const builder=page.getByTestId("portfolio-position-builder");
  await expect(builder).toBeVisible();
  await expect(page.getByTestId("portfolio-position-row")).toHaveCount(2);
  await expect(page.getByLabel("Engine input JSON")).not.toBeVisible();

  await page.getByLabel("Position 1 quantity").fill("2.5");
  await page.getByLabel("Remove position 2").click();
  await expect(page.getByTestId("portfolio-position-row")).toHaveCount(1);
  await expect(page.getByLabel("Remove position 1")).toBeDisabled();

  await page.getByRole("button",{name:"Add position"}).click();
  await page.getByLabel("Position 2 CoinGecko asset ID").fill("chainlink");
  await page.getByLabel("Position 2 symbol").fill("LINK");
  await page.getByLabel("Position 2 quantity").fill("100");
  await page.getByRole("button",{name:"Run F1"}).click();

  await expect(page.getByTestId("engine-result-summary")).toContainText("UNKNOWN — NO PROVIDER EVIDENCE RECORDED");
  expect(csrf).toBe("portfolio-builder-csrf");
  expect(submitted).toMatchObject({
    demo:false,
    workspace_id:"w1",
    input:{manual_positions:[
      {coingecko_id:"ethereum",symbol:"ETH",quantity:2.5},
      {coingecko_id:"chainlink",symbol:"LINK",quantity:100},
    ]},
  });
});
