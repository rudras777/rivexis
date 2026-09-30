import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};

test("an archive completing after a workspace switch cannot leak success state into the new workspace",async({page})=>{
  const workspaces=[
    {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
    {id:"w-beta",name:"Beta Desk",role:"Analyst",access_role:"OWNER"},
  ];
  let releasePatch:()=>void=()=>{};
  const patchGate=new Promise<void>(resolve=>{releasePatch=resolve});

  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:workspaces})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"saved-switch-csrf"})}));
  await page.route(/\/api\/v1\/saved-analyses(?:\/[^?]+)?(?:\?.*)?$/,async route=>{
    const request=route.request();
    const url=new URL(request.url());
    if(request.method()==="PATCH"){
      await patchGate;
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"saved-a",workspace_id:"w-alpha",analysis_id:"analysis-a",title:"Alpha evidence",archived:true,created_at:"2026-09-30T10:00:00Z"})});
    }
    const workspaceId=url.searchParams.get("workspace_id");
    const items=workspaceId==="w-alpha"?[{id:"saved-a",workspace_id:"w-alpha",analysis_id:"analysis-a",title:"Alpha evidence",archived:false,created_at:"2026-09-30T10:00:00Z"}]:[{id:"saved-b",workspace_id:"w-beta",analysis_id:"analysis-b",title:"Beta evidence",archived:false,created_at:"2026-09-30T11:00:00Z"}];
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
  });

  await page.goto("/workspace/saved");
  await expect(page.getByRole("cell",{name:"Alpha evidence"})).toBeVisible();
  await page.getByRole("button",{name:"Archive"}).click();

  await page.getByLabel("ACTIVE WORKSPACE").selectOption("w-beta");
  await expect(page.getByRole("heading",{name:"Saved Analyses"})).toBeVisible();
  await expect(page.getByRole("cell",{name:"Beta evidence"})).toBeVisible();
  await expect(page.getByRole("cell",{name:"Alpha evidence"})).toHaveCount(0);

  releasePatch();
  await expect(page.getByText("Saved analysis archived.")).toHaveCount(0);
  await expect(page.getByRole("cell",{name:"Beta evidence"})).toBeVisible();
});
