import type {Metadata} from "next";
import "./globals.css";
import "./product.css";
import "./entry.css";
import "./completion.css";
import {PrecisionInteractions} from "@/components/PrecisionInteractions";
import {GeistSans} from "geist/font/sans";
import {Providers} from "@/components/Providers";
import {ServiceAvailability} from "@/components/ServiceAvailability";

export const metadata:Metadata={
  title:{default:"RIVEXIS — DeFi Risk & Decision Intelligence",template:"%s | RIVEXIS"},
  description:"Understand DeFi exposure, stress-test lending positions and compare capital-constrained defensive alternatives with evidence.",
  metadataBase:new URL("https://rivexis-web.rudrasingh0718.workers.dev"),
  icons:{
    icon:[{url:"/brand/rivexis-symbol.svg",type:"image/svg+xml"},{url:"/favicon.ico",type:"image/x-icon"}],
    apple:[{url:"/brand/apple-touch-icon.png",type:"image/png",sizes:"180x180"}],
  },
  openGraph:{
    title:"Rivexis — Evidence before execution",
    description:"Risk · Value · Execution · Analysis for institutional digital-asset decisions.",
    type:"website",
    url:"/",
    images:[{url:"/brand/rivexis-social.png",width:1200,height:630,alt:"RIVEXIS — Risk. Value. Execution. Analysis."}],
  },
  twitter:{card:"summary_large_image",title:"Rivexis — Evidence before execution",description:"Risk · Value · Execution · Analysis for institutional digital-asset decisions.",images:["/brand/rivexis-social.png"]},
};

export default function RootLayout({children}:{children:React.ReactNode}){
  const buildSha=process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA||"local";
  return <html lang="en" data-theme="dark" className={GeistSans.variable}><head><meta name="rivexis-build" content={buildSha}/></head><body><Providers><ServiceAvailability/><PrecisionInteractions/>{children}</Providers></body></html>;
}
