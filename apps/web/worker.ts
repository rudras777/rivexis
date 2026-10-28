import runtime from 'vinext/server/fetch-handler';
import {publicDocument} from './lib/public-document';

type Environment={ASSETS:{fetch(request:Request):Promise<Response>};RIVEXIS_BUILD_RENDER?:string};
export default {
 async fetch(request:Request,env:Environment,ctx:unknown){
  // This local build-only binding is never present in the deployed config.
  // Request headers/query parameters cannot enable it.
  if(env.RIVEXIS_BUILD_RENDER!=='1'){
   const document=await publicDocument(request,env.ASSETS);
   if(document)return document;
  }
  return runtime.fetch(request,env,ctx);
 },
};
