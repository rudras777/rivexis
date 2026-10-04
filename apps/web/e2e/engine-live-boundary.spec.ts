import {expect,test} from "@playwright/test";

const sample="0x1111111111111111111111111111111111111111";
const explicit="0x3333333333333333333333333333333333333333";

test("non-demo analysis rejects sample EVM identities before any upstream call",async({request})=>{
  const response=await request.post("/api/v1/analysis/simulations",{
    data:{demo:false,input:{chain:"ethereum",from:sample,to:explicit},workspace_id:"w-safety"},
  });
  expect(response.status()).toBe(422);
  await expect(response.json()).resolves.toMatchObject({detail:"Replace the sample EVM addresses before submitting a non-demo analysis request."});
});

test("explicit non-demo identities pass the sample-address guard and reach the local upstream block",async({request})=>{
  const response=await request.post("/api/v1/analysis/simulations",{
    data:{demo:false,input:{chain:"ethereum",from:explicit,to:"0x4444444444444444444444444444444444444444"},workspace_id:"w-safety"},
  });
  expect(response.status()).toBe(503);
  await expect(response.json()).resolves.toMatchObject({detail:"External API upstream disabled in local E2E"});
});
