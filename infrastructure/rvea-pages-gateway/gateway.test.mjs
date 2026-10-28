import test from "node:test";
import assert from "node:assert/strict";
import gateway from "./public/_worker.js";

const live = "https://rivexis.rvea.info";
const preview = "https://rvea-rivexis-gateway.pages.dev";

function service() {
  const calls = [];
  return {
    calls,
    env: {
      RIVEXIS_WEB: {
        async fetch(request) {
          calls.push(request);
          return new Response("RIVEXIS original Worker", {
            status: 200,
            headers: {
              "content-type": "text/plain",
              "set-cookie": "rvx_session=example; Path=/; HttpOnly; Secure; SameSite=Lax"
            }
          });
        }
      }
    }
  };
}

test("custom host reaches original Worker without redirecting or changing cookies", async () => {
  const upstream = service();
  const request = new Request(live + "/workspace?tab=reports", {
    headers: {cookie: "rvx_session=example"}
  });
  const result = await gateway.fetch(request, upstream.env);
  assert.equal(result.status, 200);
  assert.equal(result.headers.get("set-cookie"), "rvx_session=example; Path=/; HttpOnly; Secure; SameSite=Lax");
  assert.equal(upstream.calls.length, 1);
  assert.equal(upstream.calls[0].url, request.url);
  assert.equal(upstream.calls[0].headers.get("cookie"), "rvx_session=example");
});

test("POST and body are forwarded on the official RVEA hostname", async () => {
  const upstream = service();
  const body = JSON.stringify({hello: "world"});
  const result = await gateway.fetch(new Request(live + "/api/v1/auth/login", {
    method: "POST",
    headers: {"content-type": "application/json", origin: live},
    body
  }), upstream.env);
  assert.equal(result.status, 200);
  assert.equal(upstream.calls[0].method, "POST");
  assert.equal(await upstream.calls[0].text(), body);
});

test("Pages preview permits public reads but rejects account changes", async () => {
  const upstream = service();
  assert.equal((await gateway.fetch(new Request(preview + "/"), upstream.env)).status, 200);
  assert.equal((await gateway.fetch(new Request(preview + "/login", {method: "POST"}), upstream.env)).status, 403);
  assert.equal((await gateway.fetch(new Request(preview + "/api/v1/account"), upstream.env)).status, 403);
  assert.equal((await gateway.fetch(new Request(preview + "/workspace", {
    headers: {cookie: "rvx_session=sensitive"}
  }), upstream.env)).status, 403);
  assert.equal(upstream.calls.length, 1);
});

test("rejects all unapproved hostnames and insecure production requests", async () => {
  const upstream = service();
  for (const url of [
    "https://rvea.info/",
    "https://attacker.example/",
    "https://rivexis.rvea.info.attacker.example/",
    "http://rivexis.rvea.info/"
  ]) {
    assert.equal((await gateway.fetch(new Request(url), upstream.env)).status, 421);
  }
  assert.equal(upstream.calls.length, 0);
});

test("missing binding fails closed and health reports 503", async () => {
  assert.equal((await gateway.fetch(new Request(live + "/"), {})).status, 503);
  const status = await gateway.fetch(new Request(preview + "/__rvea_gateway_status"), {});
  assert.equal(status.status, 503);
  assert.equal((await status.json()).ready, false);
});

test("healthy ingress reports binding readiness without leaking secrets", async () => {
  const upstream = service();
  const result = await gateway.fetch(new Request(preview + "/__rvea_gateway_status"), upstream.env);
  assert.equal(result.status, 200);
  assert.deepEqual(await result.json(), {
    service: "rvea-rivexis-gateway",
    ready: true,
    ingress: "preview"
  });
  assert.equal(upstream.calls.length, 0);
});
