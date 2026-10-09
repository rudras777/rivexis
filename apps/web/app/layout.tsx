import type {Metadata} from "next";
import "./globals.css";
import "./product.css";
import {Providers} from "@/components/Providers";
import {ServiceAvailability} from "@/components/ServiceAvailability";

export const metadata:Metadata={
  title:{default:"RIVEXIS — DeFi Risk & Decision Intelligence",template:"%s | RIVEXIS"},
  description:"Understand DeFi exposure, stress-test lending positions and compare capital-constrained defensive alternatives with evidence.",
  metadataBase:new URL("https://rivexis-web.rudrasingh0718.workers.dev"),
  icons:{
    icon:[{url:"/brand/rivexis-symbol.svg",type:"image/svg+xml"}],
    apple:[{url:"/brand/rivexis-mark.png",type:"image/png",sizes:"256x256"}],
  },
  openGraph:{
    title:"Rivexis — Evidence before execution",
    description:"Risk · Value · Execution · Analysis for institutional digital-asset decisions.",
    type:"website",
    url:"/",
    images:[{url:"/brand/rivexis-mark.png",width:256,height:256,alt:"Rivexis"}],
  },
  twitter:{card:"summary",title:"Rivexis — Evidence before execution",description:"Risk · Value · Execution · Analysis for institutional digital-asset decisions.",images:["/brand/rivexis-mark.png"]},
};

export default function RootLayout({children}:{children:React.ReactNode}){
  const buildSha=process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA||"local";
  return <html lang="en" data-theme="dark"><head><meta name="rivexis-build" content={buildSha}/></head><body><Providers><ServiceAvailability/>{children}</Providers></body></html>;
}
