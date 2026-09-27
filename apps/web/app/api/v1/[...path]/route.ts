import {proxyEdgeApi} from "@/lib/edge-api-proxy";

type Context={params:Promise<{path:string[]}>};

async function forward(request:Request,context:Context){
  const {path}=await context.params;
  return proxyEdgeApi(request,`/api/v1/${path.map(encodeURIComponent).join("/")}`);
}

export const GET=forward;
export const POST=forward;
export const PATCH=forward;
export const PUT=forward;
export const DELETE=forward;
export const OPTIONS=forward;
