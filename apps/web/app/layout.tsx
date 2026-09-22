import type {Metadata} from "next";
import "./globals.css";
import {Providers} from "@/components/Providers";
import {ServiceAvailability} from "@/components/ServiceAvailability";

export const metadata:Metadata={
  title:"Rivexis — Institutional Blockchain Risk Intelligence",
  description:"Evidence-driven blockchain intelligence and crypto-finance risk decision infrastructure."
};

export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body><Providers><ServiceAvailability/>{children}</Providers></body></html>;
}
