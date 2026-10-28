import type { NextConfig } from "next";
import {BASE_SECURITY_HEADERS} from "./lib/security-headers.mjs";
const nextConfig: NextConfig = {
  poweredByHeader:false,
  reactStrictMode:true,
  async headers(){return [{source:"/(.*)",headers:Object.entries(BASE_SECURITY_HEADERS).map(([key,value])=>({key,value}))},...['/reset-password','/login'].map(source=>({source,headers:[{key:"Referrer-Policy",value:"no-referrer"}]}))]}
};
export default nextConfig;
