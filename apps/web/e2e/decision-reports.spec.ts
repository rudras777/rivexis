import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

const decision={
  decision_id:"decision-1",decision:"MODIFY",decision_methodology_version:"1.1.0",overall_risk_score:45,
  decision_confidence:80,data_confidence:80,executive_summary:"Rivexis evaluated 2 specialist engine result(s) and returned MODIFY.",
  critical_findings:[],positive_findings:[],risk_breakdown:{B1:30,F2:60},why:["Aggregate materialized risk assessment is 45.0/100 across 2 usable specialist result(s)."],
  what_could_go_wrong:[],recommended_action:"Modify the exposure or transaction to reduce identified material risks.",safer_option:null,
  assumptions:[],missing_data:[],analysis_ids:["analysis-b1","analysis-f2"],engine_versions:{B1:"1.3.0",F2:"1.2.0"},
  engine_statuses:{B1:"COMPLETED",F2:"COMPLETED"},analysis_framework_versions:{B1:"b1-live-1.8.0",F2:"f2-live-1.4.0"},
  evidence_sources:[],unresolved_conflict_count:0,evidence_count:0,canonical_persistence_verified:true,demo:false,timestamp:"2026-09-28T14:00:00Z",
};

function analysis(id:string,engine:string,risk:number){
  return {
    analysis_id:id,engine_id:engine,engine_version:engine==="B1"?"1.3.0":"1.2.0",analysis_framework_version:engine==="B1"?"b1-live-1.8.0":"f2-live-1.4.0",
    status:"COMPLETED",severity:"moderate",risk_score:risk,data_confidence:80,engine_confidence:80,provider_consensus:"SINGLE_SOURCE",demo:false,
    summary:"Persisted specialist result.",metrics:{},signals:[],warnings:[],hard_blockers:[],mitigations:[],safer_alternatives:[],missing_data:[],provider_status:[],provider_conflicts:[],evidence:[],data_freshness:{status:"CURRENT"},assumptions:[],created_at:"2026-09-28T13:00:00Z",
  };
}

test("Decision Desk creates a canonical decision and persisted JSON HTML PDF reports",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Risk Committee",role:"Fund",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"decision-report-csrf"})}));

  let decisionCreated=false;
  await page.route("**/api/v1/history?**",route=>route.fulfill({
    status:200,contentType:"application/json",headers:corsHeaders,
    body:JSON.stringify({items:[
      ...(decisionCreated?[{type:"decision",id:"decision-1",workspace_id:"w1",created_at:"2026-09-28T14:00:00Z"}]:[]),
      {type:"analysis",id:"analysis-b1",workspace_id:"w1",engine_id:"B1",demo:false,created_at:"2026-09-28T13:00:00Z"},
      {type:"analysis",id:"analysis-b1-old",workspace_id:"w1",engine_id:"B1",demo:false,created_at:"2026-09-28T12:00:00Z"},
      {type:"analysis",id:"analysis-f2",workspace_id:"w1",engine_id:"F2",demo:false,created_at:"2026-09-28T13:05:00Z"},
    ]}),
  }));
  await page.route("**/api/v1/analyses/analysis-b1",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(analysis("analysis-b1","B1",30))}));
  await page.route("**/api/v1/analyses/analysis-f2",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(analysis("analysis-f2","F2",60))}));

  const capture:{decisionRequest:Record<string,unknown>|null;decisionCsrf:string}={decisionRequest:null,decisionCsrf:""};
  await page.route("**/api/v1/decisions/analyze",async route=>{
    capture.decisionRequest=route.request().postDataJSON() as Record<string,unknown>;
    capture.decisionCsrf=(await route.request().allHeaders())["x-rivexis-csrf"]??"";
    decisionCreated=true;
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(decision)});
  });
  await page.route("**/api/v1/decisions/decision-1",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(decision)}));

  const reportRequests:Array<{format:string;csrf:string}>=[];
  await page.route("**/api/v1/reports",async route=>{
    const input=route.request().postDataJSON() as {decision_id:string;format:string};
    const csrf=(await route.request().allHeaders())["x-rivexis-csrf"]??"";
    reportRequests.push({format:input.format,csrf});
    if(input.format==="json")return route.fulfill({status:200,contentType:"application/json",headers:{...corsHeaders,"x-rivexis-report-id":"report-json"},body:JSON.stringify({report_id:"report-json",report:decision})});
    if(input.format==="html")return route.fulfill({status:200,contentType:"text/html",headers:{...corsHeaders,"x-rivexis-report-id":"report-html"},body:"<!doctype html><title>Rivexis Report</title><h1>MODIFY</h1>"});
    return route.fulfill({status:200,contentType:"application/pdf",headers:{...corsHeaders,"x-rivexis-report-id":"report-pdf"},body:"%PDF-1.4\nRivexis decision report"});
  });

  await page.goto("/workspace/decisions");
  await expect(page.getByRole("link",{name:"Decision Desk"})).toHaveAttribute("aria-current","page");
  await expect(page.getByTestId("decision-input-selector")).toContainText("0 / 10 selected");

  const b1=page.getByLabel("Select analysis analysis-b1 for decision");
  const oldB1=page.getByLabel("Select analysis analysis-b1-old for decision");
  const f2=page.getByLabel("Select analysis analysis-f2 for decision");
  await b1.check();
  await expect(oldB1).toBeDisabled();
  await f2.check();
  await expect(page.getByTestId("decision-input-selector")).toContainText("2 / 10 selected");

  await page.getByRole("button",{name:/Create canonical decision/}).click();
  await expect(page.getByText(/Persisted decision decision-1 created from 2 canonical analysis references/)).toBeVisible();
  await expect(page.getByTestId("decision-report-workbench")).toBeVisible();
  await expect(page.getByTestId("decision-desk-detail")).toContainText("MODIFY");
  await expect(page.getByTestId("decision-desk-detail")).toContainText("Canonical persistenceVERIFIED");
  await expect(page.getByTestId("decision-desk-detail")).toContainText("analysis-b1");
  await expect(page.getByTestId("decision-desk-detail")).toContainText("analysis-f2");

  expect(capture.decisionCsrf).toBe("decision-report-csrf");
  const requestBody=capture.decisionRequest??{};
  const engineResults=Array.isArray(requestBody["engine_results"])?requestBody["engine_results"] as Array<Record<string,unknown>>:[];
  expect(engineResults.map(item=>item.analysis_id)).toEqual(["analysis-b1","analysis-f2"]);

  for(const [format,label] of [["json","Download JSON"],["html","Download HTML"],["pdf","Download PDF"]] as const){
    const download=page.waitForEvent("download");
    await page.getByRole("button",{name:label}).click();
    const file=await download;
    expect(file.suggestedFilename()).toBe(`rivexis-decision-decision-1.${format}`);
    await expect(page.getByText(`Persisted ${format.toUpperCase()} report generated for decision decision-1.`)).toBeVisible();
  }

  expect(reportRequests.map(item=>item.format)).toEqual(["json","html","pdf"]);
  expect(reportRequests.every(item=>item.csrf==="decision-report-csrf")).toBe(true);
});
