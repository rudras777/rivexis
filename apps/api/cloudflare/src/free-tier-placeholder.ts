const FRONTEND_ORIGIN = "https://rivexis-web.rudrasingh0718.workers.dev";

function corsHeaders(request: Request): HeadersInit {
  return request.headers.get("Origin") === FRONTEND_ORIGIN
    ? {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "Content-Type, X-Rivexis-CSRF",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT, PATCH, DELETE",
        "Access-Control-Allow-Origin": FRONTEND_ORIGIN,
        "Vary": "Origin",
      }
    : {};
}

export default {
  async fetch(request: Request): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    const url = new URL(request.url);
    const headers = new Headers(corsHeaders(request));
    headers.set("Cache-Control", "no-store");
    headers.set("Content-Type", "application/json; charset=utf-8");
    headers.set("X-Content-Type-Options", "nosniff");

    if (url.pathname === "/health") {
      return new Response(
        JSON.stringify({
          status: "degraded",
          service: "rivexis-api",
          reason: "FastAPI runtime unavailable on the approved free-tier stack",
        }),
        { status: 200, headers },
      );
    }

    return new Response(
      JSON.stringify({
        detail: "Rivexis application APIs are unavailable in the free-tier preview",
      }),
      { status: 503, headers },
    );
  },
} satisfies ExportedHandler;
