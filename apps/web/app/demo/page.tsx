import {DeFiWorkspace} from "@/components/DeFiWorkspace";
import {DeFiProvider} from "@/components/DeFiContext";
import {FeatureGate} from "@/components/FeatureGate";
export default function Demo(){return <DeFiProvider><FeatureGate destination="/demo"><DeFiWorkspace demoOnly/></FeatureGate></DeFiProvider>;}
