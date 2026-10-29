export const LIVE_ORIGIN="https://rivexis-web.rudrasingh0718.workers.dev";
export const PUBLIC_ORIGINS=new Set([LIVE_ORIGIN,"https://rivexis.rvea.info"]);

// Only the exact first-party browser origin can select an auth-email destination.
/** @param {Request} req */
export function authEmailOrigin(req){
  const origin=req.headers.get("origin");
  return origin!==null&&PUBLIC_ORIGINS.has(origin)?origin:LIVE_ORIGIN;
}
