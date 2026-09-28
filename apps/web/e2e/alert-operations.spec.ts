import {expect,test} from "@playwright/test";

const corsHeaders={"Access-Control-Allow-Origin":"http://127.0.0.1:3000","Access-Control-Allow-Credentials":"true"};

test("Alerts exposes scheduled queue truth and protects status/requeue actions with CSRF",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Risk Committee",role:"Fund",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/auth/web/csrf",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({csrf_token:"alerts-csrf"})}));

  let status="open";let deliveryStatus="dead_letter";
  const requests:Array<{kind:string;csrf:string}>=[];
  await page.route("**/api/v1/alerts?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:"w1",status:"durable_alert_records_only; continuous_threat_stream_not_configured; delivery_processor=scheduled_no_sink",items:[{id:"alert-1",workspace_id:"w1",monitor_id:"monitor-1",analysis_id:"analysis-1",severity:"high",status,provider_id:null,occurrence_count:1,delivery_status:deliveryStatus,delivery_attempts:5,last_delivery_error:"delivery transport unavailable",dead_lettered_at:"2026-09-28T13:10:00Z",created_at:"2026-09-28T13:00:00Z",updated_at:"2026-09-28T13:10:00Z",payload:{signals:["material change"]}}]})}));
  await page.route("**/api/v1/alerts/delivery-metrics?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:"w1",window_hours:24,slo_seconds:300,total:1,pending:deliveryStatus==="pending"?1:0,delivered:0,dead_letter:deliveryStatus==="dead_letter"?1:0,oldest_pending_age_seconds:0,delivered_within_slo_percent:null,processor_status:"SCHEDULED_NO_SINK",sink_status:"NOT_CONFIGURED",recipient_policy:"WORKSPACE_OWNER_EMAIL",last_run_at:"2026-09-28T16:30:00Z",last_processed:0,last_delivered:0,last_failed:0})}));
  await page.route("**/api/v1/alerts/alert-1?status=acknowledged",async route=>{
    requests.push({kind:"acknowledge",csrf:(await route.request().allHeaders())["x-rivexis-csrf"]??""});status="acknowledged";
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"alert-1",workspace_id:"w1",severity:"high",status,delivery_status:deliveryStatus,delivery_attempts:5,created_at:"2026-09-28T13:00:00Z",updated_at:"2026-09-28T14:00:00Z"})});
  });
  await page.route("**/api/v1/alerts/alert-1/requeue",async route=>{
    requests.push({kind:"requeue",csrf:(await route.request().allHeaders())["x-rivexis-csrf"]??""});deliveryStatus="pending";
    return route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({id:"alert-1",workspace_id:"w1",status,delivery_status:"pending",delivery_attempts:0,updated_at:"2026-09-28T14:01:00Z"})});
  });

  await page.goto("/workspace/alerts");
  await expect(page.getByRole("link",{name:"Alerts"})).toHaveAttribute("aria-current","page");
  await expect(page.getByTestId("alert-runtime-truth")).toContainText("Automatic queue scheduling is active");
  await expect(page.getByTestId("alert-runtime-truth")).toContainText("no production alert-delivery sink is configured");
  await expect(page.getByText("PROCESSOR SCHEDULED_NO_SINK")).toBeVisible();
  await expect(page.getByText("NOT_CONFIGURED",{exact:true})).toBeVisible();
  await expect(page.getByText("Workspace owner email")).toBeVisible();
  await expect(page.getByText("alert-1")).toBeVisible();
  await page.getByRole("button",{name:"Acknowledge"}).click();
  await expect.poll(()=>requests.length).toBe(1);
  await page.getByRole("button",{name:"Requeue"}).click();
  await expect.poll(()=>requests.length).toBe(2);
  expect(requests).toEqual([{kind:"acknowledge",csrf:"alerts-csrf"},{kind:"requeue",csrf:"alerts-csrf"}]);
});

test("Alerts ready state distinguishes provider acceptance from inbox delivery",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Treasury",role:"Treasury",access_role:"OWNER"}]})}));
  await page.route("**/api/v1/alerts?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:"w1",items:[],status:"durable_alert_records_only"})}));
  await page.route("**/api/v1/alerts/delivery-metrics?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:"w1",window_hours:24,slo_seconds:300,total:0,pending:0,delivered:0,dead_letter:0,oldest_pending_age_seconds:0,delivered_within_slo_percent:null,processor_status:"SCHEDULED_READY",sink_status:"BREVO_READY",recipient_policy:"WORKSPACE_OWNER_EMAIL",last_run_at:"2026-09-28T16:31:00Z",last_processed:0,last_delivered:0,last_failed:0})}));
  await page.goto("/workspace/alerts");
  await expect(page.getByTestId("alert-runtime-truth")).toContainText("Brevo submissions are enabled");
  await expect(page.getByTestId("alert-runtime-truth")).toContainText("provider acceptance, not proof of inbox delivery");
});

test("Alerts empty state does not claim absence of threats",async({page})=>{
  await page.route("**/health",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({status:"ready"})}));
  await page.route("**/api/v1/workspaces",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({items:[{id:"w1",name:"Risk Committee",role:"Fund",access_role:"VIEWER"}]})}));
  await page.route("**/api/v1/alerts?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:"w1",items:[],status:"durable_alert_records_only"})}));
  await page.route("**/api/v1/alerts/delivery-metrics?**",route=>route.fulfill({status:200,contentType:"application/json",headers:corsHeaders,body:JSON.stringify({workspace_id:"w1",window_hours:24,slo_seconds:300,total:0,pending:0,delivered:0,dead_letter:0,oldest_pending_age_seconds:0,delivered_within_slo_percent:null,processor_status:"NOT_CONFIGURED",sink_status:"NOT_CONFIGURED"})}));
  await page.goto("/workspace/alerts");
  await expect(page.getByText("No durable alerts are recorded in this workspace.")).toBeVisible();
  await expect(page.getByText(/This is not evidence that no threats exist/)).toBeVisible();
});
