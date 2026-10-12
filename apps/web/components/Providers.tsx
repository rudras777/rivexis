"use client";
import {QueryClient,QueryClientProvider} from "@tanstack/react-query";
import {useState} from "react";
import {AccountPreferencesProvider} from "./AccountPreferences";
import {WalletConnectionProvider} from "./WalletConnection";
import {MarketContextProvider} from "./MarketContext";
import {DeFiProvider} from "./DeFiContext";
export function Providers({children}:{children:React.ReactNode}){const [q]=useState(()=>new QueryClient({defaultOptions:{queries:{staleTime:15_000,retry:1}}}));return <QueryClientProvider client={q}><AccountPreferencesProvider><WalletConnectionProvider><DeFiProvider><MarketContextProvider>{children}</MarketContextProvider></DeFiProvider></WalletConnectionProvider></AccountPreferencesProvider></QueryClientProvider>}
