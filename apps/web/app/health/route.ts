import {proxyEdgeApi} from "@/lib/edge-api-proxy";

export function GET(request:Request){
  return proxyEdgeApi(request,"/health");
}
