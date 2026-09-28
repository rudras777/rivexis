import {expect,test} from "@playwright/test";

const corsHeaders={
  "Access-Control-Allow-Origin":"http://127.0.0.1:3000",
  "Access-Control-Allow-Credentials":"true",
};
const workspace={id:"w-alpha",name:"Alpha Desk",role:"Analyst",access_role:"OWNER"};

async function baseMocks(page:import("@playwright/test").Page){
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[workspace]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"protocol-operations-csrf"})}));
}

test.describe("protocol evidence operations",()=>{
  test("validates, persists and approves a configuration review",async({page})=>{
    await baseMocks(page);
    let compareBody:Record<string,unknown>|null=null;
    const unsafeHeaders:string[]=[];
    await page.route("**/api/v1/protocol-config/compare",route=>{
      compareBody=route.request().postDataJSON() as Record<string,unknown>;
      unsafeHeaders.push(route.request().headers()["x-rivexis-csrf"]??"");
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({
        event_count:0,change_count:1,materiality_counts:{HIGH:1,MEDIUM:0,LOW:0},
        changes:[{path:"reserve.borrow_cap",from:"1000000",to:"1250000",materiality:"HIGH"}],
      })});
    });
    await page.route("**/api/v1/protocol-config/reviews",route=>{
      unsafeHeaders.push(route.request().headers()["x-rivexis-csrf"]??"");
      return route.fulfill({status:201,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"review-1",status:"draft"})});
    });
    await page.route("**/api/v1/protocol-config/reviews/review-1/approve",route=>{
      unsafeHeaders.push(route.request().headers()["x-rivexis-csrf"]??"");
      return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"review-1",status:"approved",approved_at:"2026-09-28T12:00:00Z"})});
    });

    await page.goto("/workspace/protocol-history");
    const compare=page.getByRole("button",{name:"Compare configuration"});
    await expect(compare).toBeDisabled();
    await page.getByLabel("From block").fill("21000100");
    await page.getByLabel("To block").fill("21000000");
    await expect(page.getByText("Enter a complete block range with the from block less than or equal to the to block.")).toBeVisible();
    await expect(compare).toBeDisabled();
    await page.getByLabel("To block").fill("21000200");
    await expect(compare).toBeEnabled();
    await compare.click();

    const result=page.getByTestId("protocol-history-result");
    await expect(result).toContainText("reserve.borrow_cap");
    await expect(result).toContainText("High materiality");
    await page.getByRole("button",{name:"Save review artifact"}).click();
    const review=page.getByTestId("protocol-review");
    await expect(review).toContainText("review-1");
    await expect(review.getByRole("link",{name:"Open PDF report"})).toHaveAttribute("href","/api/v1/protocol-config/reviews/review-1/render?format=pdf");
    await review.getByRole("button",{name:"Approve review"}).click();
    await expect(review).toContainText(/approved/i);

    expect(compareBody).toMatchObject({workspace_id:"w-alpha",input:{protocol_adapter:"aave_v3",chain:"ethereum",from_block:"21000100",to_block:"21000200",hydrate_timestamps:true}});
    expect(unsafeHeaders).toEqual(["protocol-operations-csrf","protocol-operations-csrf","protocol-operations-csrf"]);
  });

  test("creates, links and closes an investigation with an explicit disposition",async({page})=>{
    await baseMocks(page);
    let current:{id:string;status:string;created_at:string;payload:Record<string,unknown>}|null=null;
    let createBody:Record<string,unknown>|null=null;
    const unsafeHeaders:string[]=[];
    await page.route(/\/api\/v1\/protocol-investigations(?:\/.*|\?.*)?$/,route=>{
      const request=route.request();
      const path=new URL(request.url()).pathname;
      const csrf=request.headers()["x-rivexis-csrf"]??"";
      if(request.method()==="GET")return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:current?[current]:[]})});
      unsafeHeaders.push(csrf);
      if(request.method()==="POST"&&path.endsWith("/reviews/review-1")){
        if(current)current={...current,payload:{...current.payload,review_ids:["review-1"]}};
        return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(current)});
      }
      if(request.method()==="PATCH"){
        const body=request.postDataJSON() as {status:string;notes:string;disposition:string};
        if(current)current={...current,status:body.status,payload:{...current.payload,notes:body.notes,disposition:body.disposition}};
        return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(current)});
      }
      createBody=request.postDataJSON() as Record<string,unknown>;
      const body=createBody as {title:string;notes:string};
      current={id:"case-1",status:"open",created_at:"2026-09-28T12:00:00Z",payload:{title:body.title,notes:body.notes,review_ids:[],timeline:{event_count:0}}};
      return route.fulfill({status:201,contentType:"application/json",headers:corsHeaders,body:JSON.stringify(current)});
    });

    await page.goto("/workspace/investigations");
    const create=page.getByRole("button",{name:"Create investigation"});
    await expect(create).toBeDisabled();
    await page.getByLabel("Case title").fill("Aave WETH parameter review");
    await page.getByLabel("From block").fill("21000100");
    await page.getByLabel("To block").fill("21000000");
    await expect(create).toBeDisabled();
    await page.getByLabel("To block").fill("21000200");
    await page.getByLabel("Opening notes").fill("Confirm the bounded configuration change and retain uncertainty.");
    await expect(create).toBeEnabled();
    await create.click();

    const selected=page.getByTestId("investigation-selected");
    await expect(selected).toContainText("case-1");
    await expect(selected.getByRole("link",{name:"Open PDF report"})).toHaveAttribute("href","/api/v1/protocol-investigations/case-1/render?format=pdf");
    await selected.getByLabel("Configuration review ID").fill("review-1");
    await selected.getByRole("button",{name:"Attach review"}).click();
    await expect(selected).toContainText("review-1");
    await selected.getByLabel("Disposition").fill("Configuration change confirmed; downstream impact remains separately assessed.");
    await selected.getByRole("button",{name:"Close with disposition"}).click();
    await expect(selected).toContainText(/closed/i);

    expect(createBody).toMatchObject({workspace_id:"w-alpha",title:"Aave WETH parameter review",input:{protocol_adapter:"aave_v3",chain:"ethereum",from_block:"21000100",to_block:"21000200",hydrate_timestamps:true}});
    expect(unsafeHeaders).toEqual(["protocol-operations-csrf","protocol-operations-csrf","protocol-operations-csrf"]);
  });
});
