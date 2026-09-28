import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};
const workspace={id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"};

async function baseMocks(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[workspace]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"operational-surface-csrf"})}));
}

test.describe("institutional operational surfaces",()=>{
  test("provider control plane preserves configuration and deep-probe truth",async({page})=>{
    await baseMocks(page);
    const requestedModes:boolean[]=[];
    await page.route("**/api/v1/providers/status?**",route=>{
      const deep=new URL(route.request().url()).searchParams.get("deep")==="true";
      requestedModes.push(deep);
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
        chain:"ethereum",deep_probe_available:true,
        providers:[{provider_id:"ethereum_rpc",status:deep?"HEALTHY":"CONFIGURED",configured:true,latency_ms:deep?82:undefined,block_number:deep?22123456:undefined}],
      })});
    });
    await page.route("**/api/v1/providers/runtime?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({scope:"w-alpha",control_backend:"postgres",providers:{ethereum_rpc:{logical_calls:4,attempts:4,successes:4,failures:0,cache_hits:1,circuit:{state:"CLOSED"}}}})}));

    await page.goto("/workspace/providers");
    await expect(page.getByRole("heading",{name:"Provider health"})).toBeVisible();
    await expect(page.getByText("Does not imply connectivity")).toBeVisible();
    await expect(page.getByTestId("workspace-provider-runtime")).toContainText("postgres");
    await expect(page.getByTestId("workspace-provider-runtime")).toContainText("CLOSED");
    await page.getByRole("button",{name:"Run deep RPC probe"}).click();
    await expect(page.getByRole("button",{name:"Return to configuration"})).toBeVisible();
    await expect(page.getByText("82 ms")).toBeVisible();
    await expect.poll(()=>requestedModes).toContain(true);
  });

  test("monitor creation validates identity and renders a normalized B3 check",async({page})=>{
    await baseMocks(page);
    const monitors:Array<Record<string,unknown>>=[];
    let createBody:Record<string,unknown>|null=null;
    let createCsrf="";
    await page.route(/\/api\/v1\/monitors(?:\?.*)?$/,route=>{
      if(route.request().method()==="POST"){
        createBody=route.request().postDataJSON() as Record<string,unknown>;
        createCsrf=route.request().headers()["x-rivexis-csrf"]??"";
        const monitor={id:"m-1",entity:(createBody as {entity:string}).entity,chain:(createBody as {chain:string}).chain,status:"active",last_status:null,last_analysis_id:null};
        monitors.push(monitor);
        return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(monitor)});
      }
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:monitors})});
    });
    await page.route("**/api/v1/monitors/m-1/check",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({analysis_id:"analysis-b3-1",status:"PARTIAL",risk_score:37,severity:"moderate",summary:"A bounded snapshot comparison completed.",signals:[{type:"balance_change"}],metrics:{},missing_data:["independent threat feed"]})}));

    await page.goto("/workspace/monitors");
    const create=page.getByRole("button",{name:"Create monitor"});
    await expect(create).toBeDisabled();
    await page.getByLabel("Entity address").fill("0x1234");
    await expect(page.getByText("Enter a full 0x-prefixed 20-byte EVM address.")).toBeVisible();
    await expect(create).toBeDisabled();
    await page.getByLabel("Entity address").fill("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    await expect(create).toBeEnabled();
    await create.click();
    await expect(page.getByText("0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")).toBeVisible();
    expect(createBody).toMatchObject({workspace_id:"w-alpha",chain:"ethereum",rules:["balance_change","bytecode_change"]});
    expect(createCsrf).toBe("operational-surface-csrf");

    await page.getByRole("button",{name:"Check now"}).click();
    const result=page.getByTestId("monitor-latest-result");
    await expect(result).toContainText("ON-DEMAND B3 RESULT");
    await expect(result).toContainText("PARTIAL");
    await expect(result).toContainText("37");
    await expect(result).toContainText("independent threat feed");
    await expect(result.locator("details")).not.toHaveAttribute("open");
  });
});
