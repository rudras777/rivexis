import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("monitor check renders provider-unavailable UNKNOWN without inventing a risk score",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Research Desk",role:"Analyst",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"monitor-boundary-csrf"})}));
  await page.route(/\/api\/v1\/monitors(?:\?.*)?$/,route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"m-1",entity:"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",chain:"ethereum",status:"active",last_status:null,last_analysis_id:null}]})}));
  await page.route("**/api/v1/monitors/m-1/check",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
    analysis_id:"analysis-unknown",status:"UNKNOWN",risk_score:null,severity:"unknown",
    summary:"No verified live provider evidence is configured for this free runtime; Rivexis returns UNKNOWN rather than fabricating a result.",
    signals:[],metrics:{},missing_data:["verified live provider evidence"],
  })}));

  await page.goto("/workspace/monitors");
  await expect(page.getByText(/current free Edge runtime has no verified provider source configured/)).toBeVisible();
  await page.getByRole("button",{name:"Check now"}).click();

  const result=page.getByTestId("monitor-latest-result");
  await expect(result).toContainText("UNKNOWN");
  await expect(result).toContainText("Latest evidence request");
  await expect(result).toContainText("verified live provider evidence");
  const score=result.locator(".resultScore");
  await expect(score).toContainText("RISK SCORE");
  await expect(score).toContainText("—");
  await expect(score).not.toContainText("/100");
});
