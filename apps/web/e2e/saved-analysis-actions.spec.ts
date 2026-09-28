import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};
const workspace={id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"};

test("saved analyses support inspect, archive, restore, search and delete",async({page})=>{
  const items=[
    {id:"saved-1",workspace_id:"w-alpha",analysis_id:"analysis-alpha",title:"Alpha security review",archived:false,created_at:"2026-09-23T07:00:00Z"},
    {id:"saved-2",workspace_id:"w-alpha",analysis_id:"analysis-beta",title:"Beta protocol review",archived:true,created_at:"2026-09-23T08:00:00Z"},
  ];
  const mutations:Array<{method:string;url:string;csrf:string}>=[];

  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[workspace]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"saved-actions-csrf"})}));
  await page.route(/\/api\/v1\/saved-analyses(?:\/[^?]+)?(?:\?.*)?$/,route=>{
    const request=route.request();
    const url=new URL(request.url());
    const method=request.method();
    const parts=url.pathname.split("/").filter(Boolean);
    const id=parts.length>3?parts.at(-1):null;
    if(method==="GET"){
      const includeArchived=url.searchParams.get("include_archived")==="true";
      const visible=items.filter(item=>includeArchived||!item.archived);
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:visible})});
    }
    mutations.push({method,url:request.url(),csrf:request.headers()["x-rivexis-csrf"]??""});
    if(method==="PATCH"&&id){
      const item=items.find(candidate=>candidate.id===id)!;
      item.archived=url.searchParams.get("archived")==="true";
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(item)});
    }
    if(method==="DELETE"&&id){
      const index=items.findIndex(candidate=>candidate.id===id);
      if(index>=0)items.splice(index,1);
      return route.fulfill({status:204,headers:corsHeaders,body:""});
    }
    return route.fulfill({status:405,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({detail:"Method not allowed"})});
  });
  await page.route("**/api/v1/analyses/analysis-alpha",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
    analysis_id:"analysis-alpha",engine_id:"B2",engine_version:"2.2.0",status:"PARTIAL",risk_score:47,data_confidence:70,demo:false,
    provider_consensus:"SINGLE_SOURCE",evidence:[{provider:"ethereum_rpc",source_type:"direct_state"}],missing_data:["indexed approval history"],
  })}));

  await page.goto("/workspace/saved");
  await expect(page.getByRole("cell",{name:"Alpha security review"})).toBeVisible();
  await expect(page.getByText("Beta protocol review")).toHaveCount(0);

  await page.getByLabel("Search saved analyses").fill("security");
  await expect(page.getByRole("cell",{name:"Alpha security review"})).toBeVisible();
  await page.getByLabel("Search saved analyses").fill("protocol");
  await expect(page.getByText("No saved analyses match the current search and visibility filters.")).toBeVisible();
  await page.getByLabel("Search saved analyses").fill("");

  await page.getByRole("button",{name:"Inspect evidence"}).click();
  const detail=page.getByTestId("saved-analysis-detail");
  await expect(detail).toContainText("Alpha security review");
  await expect(detail).toContainText("StatusPARTIAL");
  await expect(detail).toContainText("EngineB2");
  await expect(detail).toContainText("Risk score47/100");
  await expect(detail).toContainText("indexed approval history");

  await page.getByRole("button",{name:"Archive"}).click();
  await expect(page.getByText("Saved analysis archived.")).toBeVisible();
  await expect(page.getByRole("cell",{name:"Alpha security review"})).toHaveCount(0);

  await page.getByLabel("Saved analysis visibility").selectOption("all");
  await expect(page.getByRole("cell",{name:"Alpha security review"})).toBeVisible();
  await expect(page.getByRole("cell",{name:"Beta protocol review"})).toBeVisible();
  const alphaRow=page.getByRole("row").filter({has:page.getByRole("cell",{name:"Alpha security review"})});
  await alphaRow.getByRole("button",{name:"Restore"}).click();
  await expect(page.getByText("Saved analysis restored to the active list.")).toBeVisible();
  await expect(alphaRow).toContainText("Active");

  await alphaRow.getByRole("button",{name:"Delete"}).click();
  await alphaRow.getByRole("button",{name:"Confirm delete"}).click();
  await expect(page.getByText("Saved reference deleted. The underlying persisted analysis remains in workspace history.")).toBeVisible();
  await expect(page.getByRole("cell",{name:"Alpha security review"})).toHaveCount(0);

  expect(mutations).toHaveLength(3);
  expect(mutations.map(item=>item.method)).toEqual(["PATCH","PATCH","DELETE"]);
  expect(mutations.every(item=>item.csrf==="saved-actions-csrf")).toBeTruthy();
  expect(mutations[0].url).toContain("archived=true");
  expect(mutations[1].url).toContain("archived=false");
});
