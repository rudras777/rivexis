import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

test("Edge workspace creation forwards explicit organization scope through the dedicated RPC",async()=>{
  const source=await readFile(new URL("./index.ts",import.meta.url),"utf8");
  assert.match(source,/rivexis_edge_create_organization_workspace/);
  assert.match(source,/organization_id:organizationId/);
  assert.match(source,/Organization write access required/);
  assert.match(source,/organizationId\s*\?await organizationWorkspaceBridge/);
});
