import test from "node:test";
import assert from "node:assert/strict";
import {parseRole,roleOrDefault,RIVEXIS_ROLES} from "./role.mjs";

test("accepts only the four public Rivexis roles",()=>{
  assert.deepEqual(RIVEXIS_ROLES,["Individual","Fund","Treasury","Analyst"]);
  for(const value of RIVEXIS_ROLES)assert.equal(parseRole(value),value);
});

test("rejects malformed or unknown roles instead of silently downgrading",()=>{
  for(const value of [undefined,null,"","individual","OWNER","Admin",42,{},[]])assert.equal(parseRole(value),null);
});

test("legacy metadata may still receive an explicit safe default",()=>{
  assert.equal(roleOrDefault(undefined),"Individual");
  assert.equal(roleOrDefault("Analyst"),"Analyst");
});
