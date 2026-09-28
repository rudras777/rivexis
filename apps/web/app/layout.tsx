import type {Metadata} from "next";
import "./globals.css";
import "./institutional-ui.css";
import "./signature-ui.css";
import {Providers} from "@/components/Providers";
import {ServiceAvailability} from "@/components/ServiceAvailability";

export const metadata:Metadata={
  title:"Rivexis — Institutional Blockchain Risk Intelligence",
  description:"Evidence-driven blockchain intelligence and crypto-finance risk decision infrastructure."
};

export default function RootLayout({children}:{children:React.ReactNode}){
  const buildSha=process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA||"local";
  return <html lang="en"><head><meta name="rivexis-build" content={buildSha}/></head><body><Providers><ServiceAvailability/>{children}</Providers></body></html>;
}
