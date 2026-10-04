import {expect,test} from "@playwright/test";

test("local E2E never proxies an unmocked API request to production",async({request})=>{
  test.skip(Boolean(process.env.RIVEXIS_WEB_BASE_URL),"External smoke runs intentionally target their configured base URL.");
  const response=await request.get("/api/v1/saved-analyses?workspace_id=e2e-isolation-probe");
  expect(response.status()).toBe(503);
  await expect(response.json()).resolves.toEqual({detail:"External API upstream disabled in local E2E"});
});
