import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("a history save completing after a workspace switch cannot mark the new workspace as saved",async({page})=>{
  const workspaces=[
    {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
    {id:"w-beta",name:"Beta Desk",role:"Analyst",access_role:"OWNER"},
  ];
  let releaseSave:()=>void=()=>{};
  const saveGate=new Promise<void>(resolve=>{releaseSave=resolve});

  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:workspaces})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"history-switch-csrf"})}));
  await page.route("**/api/v1/history?**",route=>{
    const workspaceId=new URL(route.request().url()).searchParams.get("workspace_id");
    const row=workspaceId==="w-alpha"
      ? {type:"analysis",id:"analysis-alpha",workspace_id:"w-alpha",engine_id:"B2",demo:false,created_at:"2026-09-30T10:00:00Z"}
      : {type:"analysis",id:"analysis-beta",workspace_id:"w-beta",engine_id:"B3",demo:false,created_at:"2026-09-30T11:00:00Z"};
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[row]})});
  });
  await page.route(/\/api\/v1\/saved-analyses(?:\?.*)?$/,async route=>{
    if(route.request().method()==="POST"){
      const body=route.request().postDataJSON() as {analysis_id:string;title:string};
      await saveGate;
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"saved-alpha",workspace_id:"w-alpha",analysis_id:body.analysis_id,title:body.title,archived:false,created_at:"2026-09-30T10:01:00Z"})});
    }
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[]})});
  });

  await page.goto("/workspace/history");
  await expect(page.getByText("analysis-alpha",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Save reference"}).click();

  await page.getByLabel("ACTIVE WORKSPACE").selectOption("w-beta");
  await expect(page.getByText("analysis-beta",{exact:true})).toBeVisible();
  await expect(page.getByText("analysis-alpha",{exact:true})).toHaveCount(0);

  releaseSave();
  await expect(page.getByText(/Saved analysis-alpha as/)).toHaveCount(0);
  await expect(page.getByRole("button",{name:"Save reference"})).toBeVisible();
});
