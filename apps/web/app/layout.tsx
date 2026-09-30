import type {Metadata} from "next";
import "./globals.css";
import "./institutional-ui.css";
import "./signature-ui.css";
import "./royal-obsidian.css";
import {Providers} from "@/components/Providers";
import {ServiceAvailability} from "@/components/ServiceAvailability";

export const metadata:Metadata={
  title:"Rivexis — Institutional Blockchain Risk Intelligence",
  description:"Evidence-driven blockchain intelligence and crypto-finance risk decision infrastructure.",
  metadataBase:new URL("https://rivexis-web.rudrasingh0718.workers.dev"),
  icons:{
    icon:[{url:"/brand/rivexis-icon.png",type:"image/png",sizes:"256x256"}],
    apple:[{url:"/brand/rivexis-icon.png",type:"image/png",sizes:"256x256"}],
  },
  openGraph:{
    title:"Rivexis — Evidence before execution",
    description:"Risk · Value · Execution · Analysis for institutional digital-asset decisions.",
    type:"website",
    url:"/",
    images:[{url:"/brand/rivexis-icon.png",width:256,height:256,alt:"Rivexis"}],
  },
  twitter:{card:"summary",title:"Rivexis — Evidence before execution",description:"Risk · Value · Execution · Analysis for institutional digital-asset decisions.",images:["/brand/rivexis-icon.png"]},
};

export default function RootLayout({children}:{children:React.ReactNode}){
  const buildSha=process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA||"local";
  return <html lang="en"><head><meta name="rivexis-build" content={buildSha}/></head><body><Providers><ServiceAvailability/>{children}</Providers></body></html>;
}
