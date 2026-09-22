import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};
const workspaces=[
  {id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"},
  {id:"w-beta",name:"Beta Desk",role:"Analyst",access_role:"ANALYST"},
];

async function baseMocks(page:import("@playwright/test").Page,onWorkspaceCall?:()=>void){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>{
    onWorkspaceCall?.();
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:workspaces})});
  });
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"workspace-switch-csrf"})}));
}

function workspaceSelector(page:import("@playwright/test").Page){
  return page.getByRole("combobox",{name:"ACTIVE WORKSPACE"});
}

test.describe("in-place workspace switching",()=>{
  test("discards an engine result that completes after its workspace is no longer active",async({page})=>{
    let workspaceCalls=0;
    await baseMocks(page,()=>workspaceCalls+=1);
    await page.route("**/api/v1/analysis/security",async route=>{
      const body=route.request().postDataJSON() as {workspace_id:string};
      if(body.workspace_id==="w-alpha")await new Promise(resolve=>setTimeout(resolve,450));
      return route.fulfill({
        status:200,contentType:"application/json",headers:corsHeaders,
        body:JSON.stringify({analysis_id:`analysis-${body.workspace_id}`,demo:true,status:"PROCEED",marker:body.workspace_id==="w-alpha"?"ALPHA_ENGINE_RESULT":"BETA_ENGINE_RESULT"}),
      });
    });

    await page.goto("/workspace/engines/B2");
    await expect(workspaceSelector(page)).toHaveValue("w-alpha");
    await page.getByRole("button",{name:"Run B2"}).click();
    await workspaceSelector(page).selectOption("w-beta");
    await expect(workspaceSelector(page)).toHaveValue("w-beta");
    await page.waitForTimeout(650);
    await expect(page.getByText("ALPHA_ENGINE_RESULT")).toHaveCount(0);
    await expect(page.getByTestId("engine-result")).toHaveCount(0);
    expect(workspaceCalls).toBe(1);

    await page.getByRole("button",{name:"Run B2"}).click();
    await expect(page.getByTestId("engine-result")).toContainText("BETA_ENGINE_RESULT");
    await expect(page.getByText("ALPHA_ENGINE_RESULT")).toHaveCount(0);
  });

  test("clears a delayed monitor result and refetches the monitor list for the new workspace",async({page})=>{
    let workspaceCalls=0;
    await baseMocks(page,()=>workspaceCalls+=1);
    await page.route("**/api/v1/monitors?**",route=>{
      const id=new URL(route.request().url()).searchParams.get("workspace_id");
      const items=id==="w-alpha"?[{id:"m-alpha",entity:"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",chain:"ethereum",status:"active",last_status:null}]:[];
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items})});
    });
    await page.route("**/api/v1/monitors/m-alpha/check",async route=>{
      await new Promise(resolve=>setTimeout(resolve,450));
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({analysis_id:"alpha-monitor-result",status:"MODIFY",risk_score:61,severity:"high",summary:"ALPHA_MONITOR_RESULT",signals:[],metrics:{},missing_data:[]})});
    });

    await page.goto("/workspace/monitors");
    await expect(page.getByText("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")).toBeVisible();
    await page.getByRole("button",{name:"Check now"}).click();
    await workspaceSelector(page).selectOption("w-beta");
    await expect(page.getByTestId("workspace-monitors-state")).toContainText("No monitors are configured in this workspace yet.");
    await page.waitForTimeout(650);
    await expect(page.getByText("ALPHA_MONITOR_RESULT")).toHaveCount(0);
    await expect(page.getByTestId("monitor-latest-result")).toHaveCount(0);
    expect(workspaceCalls).toBe(1);
  });

  test("clears an investigation selection when workspace identity changes",async({page})=>{
    let workspaceCalls=0;
    await baseMocks(page,()=>workspaceCalls+=1);
    await page.route("**/api/v1/protocol-investigations?**",route=>{
      const id=new URL(route.request().url()).searchParams.get("workspace_id");
      const items=id==="w-alpha"?[{id:"case-alpha",status:"open",created_at:"2026-09-23T00:00:00Z",payload:{title:"ALPHA_CASE",notes:"alpha",review_ids:[],timeline:{event_count:1}}}]:[];
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:id,items})});
    });

    await page.goto("/workspace/investigations");
    await page.getByText("ALPHA_CASE",{exact:true}).click();
    await expect(page.getByTestId("investigation-selected")).toContainText("case-alpha");
    await workspaceSelector(page).selectOption("w-beta");
    await expect(page.getByTestId("workspace-investigations-state")).toContainText("No investigation cases in this workspace.");
    await expect(page.getByTestId("investigation-selected")).toHaveCount(0);
    await expect(page.getByText("ALPHA_CASE",{exact:true})).toHaveCount(0);
    expect(workspaceCalls).toBe(1);
  });

  test("ignores a protocol-history response that returns after a workspace switch",async({page})=>{
    let workspaceCalls=0;
    await baseMocks(page,()=>workspaceCalls+=1);
    await page.route("**/api/v1/protocol-config/compare",async route=>{
      const body=route.request().postDataJSON() as {workspace_id:string};
      if(body.workspace_id==="w-alpha")await new Promise(resolve=>setTimeout(resolve,450));
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({change_count:1,changes:[],marker:body.workspace_id==="w-alpha"?"ALPHA_PROTOCOL_RESULT":"BETA_PROTOCOL_RESULT"})});
    });

    await page.goto("/workspace/protocol-history");
    await page.getByLabel("From block").fill("21000000");
    await page.getByLabel("To block").fill("21000001");
    await page.getByRole("button",{name:"Compare configuration"}).click();
    await workspaceSelector(page).selectOption("w-beta");
    await page.waitForTimeout(650);
    await expect(page.getByText("ALPHA_PROTOCOL_RESULT")).toHaveCount(0);
    await expect(page.getByTestId("protocol-history-result")).toHaveCount(0);
    expect(workspaceCalls).toBe(1);

    await page.getByRole("button",{name:"Compare configuration"}).click();
    await expect(page.getByTestId("protocol-history-result")).toContainText("BETA_PROTOCOL_RESULT");
    await expect(page.getByText("ALPHA_PROTOCOL_RESULT")).toHaveCount(0);
  });
});
