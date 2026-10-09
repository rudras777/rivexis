"use client";
import {QueryClient,QueryClientProvider} from "@tanstack/react-query";
import {useEffect,useState} from "react";
import {DeFiProvider} from "./DeFiContext";
export function Providers({children}:{children:React.ReactNode}){const [q]=useState(()=>new QueryClient({defaultOptions:{queries:{staleTime:15_000,retry:1}}}));useEffect(()=>{document.documentElement.dataset.theme=localStorage.getItem("rivexis_theme")==="light"?"light":"dark"},[]);return <QueryClientProvider client={q}><DeFiProvider>{children}</DeFiProvider></QueryClientProvider>}
