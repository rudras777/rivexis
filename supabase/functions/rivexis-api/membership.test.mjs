import test from "node:test";
import assert from "node:assert/strict";
import {createMembershipClaimToken,hashMembershipClaimToken} from "./membership.mjs";

test("membership claims are high-entropy opaque base64url values",()=>{
  const first=createMembershipClaimToken();
  const second=createMembershipClaimToken();
  assert.match(first,/^[A-Za-z0-9_-]{43}$/);
  assert.match(second,/^[A-Za-z0-9_-]{43}$/);
  assert.notEqual(first,second);
});

test("membership claim hashing is deterministic and does not expose the raw token",async()=>{
  const token="abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG";
  const first=await hashMembershipClaimToken(token);
  const second=await hashMembershipClaimToken(token);
  assert.equal(first,second);
  assert.match(first,/^[0-9a-f]{64}$/);
  assert.notEqual(first,token);
});

test("membership claim hashing rejects malformed short tokens",async()=>{
  await assert.rejects(()=>hashMembershipClaimToken("short"),/Invalid membership claim token/);
});
