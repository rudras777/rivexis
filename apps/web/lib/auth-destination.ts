const destinations=new Set(["/workspace","/workspace/scenarios","/workspace/frontier","/workspace/transactions","/workspace/reports","/workspace/history","/workspace/settings","/app"]);
export function safeDestination(value:unknown){return typeof value==="string"&&destinations.has(value)?value:"/workspace";}
export function intendedDestination(){
  if(typeof window==="undefined")return "/workspace";
  const requested=new URLSearchParams(window.location.search).get("next");
  return safeDestination(requested??sessionStorage.getItem("rivexis_pending_destination"));
}
export function authHref(path:"/login"|"/signup"|"/verify-email"|"/onboarding",destination:string,extra:Record<string,string>={}){
  const params=new URLSearchParams(extra),next=safeDestination(destination);
  if(next!=="/workspace")params.set("next",next);
  return path+(params.size?`?${params}`:"");
}
