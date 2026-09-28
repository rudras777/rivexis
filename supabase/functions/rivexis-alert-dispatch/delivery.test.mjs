import test from "node:test";
import assert from "node:assert/strict";
import {alertEmail,classifyBrevo,escapeHtml,idempotencyUuid,validEmail} from "./delivery.mjs";

test("alert email is evidence-truthful and escapes provider-controlled text",()=>{
  const mail=alertEmail({
    id:"11111111-1111-4111-8111-111111111111",
    workspace_name:"Risk <Desk>",
    severity:"critical",
    status:"open",
    occurrence_count:2,
    payload:{risk_score:88,evidence_mode:"SYNTHETIC_DEMO"}
  });
  assert.match(mail.subject,/CRITICAL/);
  assert.match(mail.text,/synthetic demonstration evidence/i);
  assert.match(mail.html,/Risk &lt;Desk&gt;/);
  assert.doesNotMatch(mail.html,/Risk <Desk>/);
});

test("live alert wording never claims continuous surveillance",()=>{
  const mail=alertEmail({id:"alert-1",workspace_name:"Treasury",severity:"high",status:"open",payload:{evidence_mode:"VERIFIED_COMPATIBILITY_RESULT"}});
  assert.match(mail.text,/persisted Rivexis alert record/i);
  assert.match(mail.text,/does not imply continuous provider surveillance/i);
});

test("idempotency key is stable UUID for both UUID and legacy ids",async()=>{
  const uuid="11111111-1111-4111-8111-111111111111";
  assert.equal(await idempotencyUuid(uuid),uuid);
  const first=await idempotencyUuid("legacy-alert-id");
  const second=await idempotencyUuid("legacy-alert-id");
  assert.equal(first,second);
  assert.match(first,/^[0-9a-f-]{36}$/);
});

test("Brevo duplicate idempotency response is treated as prior acceptance",()=>{
  assert.deepEqual(classifyBrevo(201),{ok:true,duplicate:false,error_code:null});
  assert.deepEqual(classifyBrevo(400,"duplicate_parameter"),{ok:true,duplicate:true,error_code:null});
  assert.deepEqual(classifyBrevo(503),{ok:false,duplicate:false,error_code:"brevo_http_503"});
});

test("email and HTML helpers reject unsafe basics",()=>{
  assert.equal(validEmail("owner@example.com"),true);
  assert.equal(validEmail("not-an-email"),false);
  assert.equal(escapeHtml(`<script>"x"</script>`),"&lt;script&gt;&quot;x&quot;&lt;/script&gt;");
});
