// Single-purpose Cloudflare Pages ingress for the existing RIVEXIS Worker.
// No application/database/auth code or credentials are duplicated here.
const PRODUCTION_HOST = "rivexis.rvea.info";
const PREVIEW_HOST = "rvea-rivexis-gateway.pages.dev";
const HEALTH_PATH = "/__rvea_gateway_status";

function response(message, status) {
  return new Response(message, {
    status,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff"
    }
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const hostname = url.hostname.toLowerCase();
    const production = hostname === PRODUCTION_HOST && url.protocol === "https:";
    const preview = url.protocol === "https:" && (hostname === PREVIEW_HOST || hostname.endsWith("." + PREVIEW_HOST));
    const ready = typeof env?.RIVEXIS_WEB?.fetch === "function";

    if ((production || preview) && request.method === "GET" && url.pathname === HEALTH_PATH) {
      return new Response(JSON.stringify({
        service: "rvea-rivexis-gateway",
        ready,
        ingress: production ? "production" : "preview"
      }), {
        status: ready ? 200 : 503,
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "no-store",
          "x-content-type-options": "nosniff"
        }
      });
    }

    if (!production && !preview) {
      return response("Unrecognized RIVEXIS hostname", 421);
    }

    // The public Pages preview host only serves unauthenticated GET/HEAD content.
    // Do not create, inspect or share accounts on this temporary ingress.
    if (preview && (!["GET", "HEAD"].includes(request.method)
      || url.pathname.startsWith("/api/")
      || request.headers.has("cookie")
      || request.headers.has("authorization"))) {
      return response("Preview is read-only", 403);
    }

    if (!ready) {
      return response("RIVEXIS service binding unavailable", 503);
    }

    // The Fetcher binding invokes the ORIGINAL rivexis-web Worker directly.
    // Request URL, method, body, cookies and Set-Cookie stay intact, so
    // same-origin browser interactions remain on rivexis.rvea.info.
    return env.RIVEXIS_WEB.fetch(request);
  }
};
