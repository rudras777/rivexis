import test from "node:test";
import assert from "node:assert/strict";
import {LIVE_ORIGIN,authEmailOrigin} from "./public-origin.mjs";

for(const origin of [LIVE_ORIGIN,"https://rivexis.rvea.info"])test(`auth emails return to exact first-party origin ${origin}`,()=>{
  const req=new Request("https://edge.example/auth",{headers:{origin}});
  assert.equal(authEmailOrigin(req),origin);
});

test("missing browser origin keeps the legacy rollback destination and ignores forwarded headers",()=>{
  const req=new Request("https://edge.example/auth",{headers:{"x-rivexis-forwarded-origin":"https://rivexis.rvea.info"}});
  assert.equal(authEmailOrigin(req),LIVE_ORIGIN);
});

for(const origin of [
  "null",
  "https://untrusted.example",
  "https://rivexis.rvea.info.untrusted.example",
  "https://rivexis.rvea.info@untrusted.example",
  "http://rivexis.rvea.info",
  "https://rivexis.rvea.info:444",
  "https://rivexis.rvea.info/reset-password",
])test(`untrusted auth-email origin falls back safely: ${origin}`,()=>{
  const req=new Request("https://edge.example/auth",{headers:{origin}});
  assert.equal(authEmailOrigin(req),LIVE_ORIGIN);
});
