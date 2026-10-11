"use client";
import {QueryClient,QueryClientProvider} from "@tanstack/react-query";
import {useState} from "react";
import {AccountPreferencesProvider} from "./AccountPreferences";
import {DeFiProvider} from "./DeFiContext";
export function Providers({children}:{children:React.ReactNode}){const [q]=useState(()=>new QueryClient({defaultOptions:{queries:{staleTime:15_000,retry:1}}}));return <QueryClientProvider client={q}><AccountPreferencesProvider><DeFiProvider>{children}</DeFiProvider></AccountPreferencesProvider></QueryClientProvider>}
