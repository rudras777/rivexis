import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(() => new Response(
  JSON.stringify({status:"disabled", service:"rivexis-cloudflare-recovery-relay"}),
  {status:410, headers:{"content-type":"application/json","cache-control":"no-store"}}
));
