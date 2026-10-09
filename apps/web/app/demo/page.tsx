import {DeFiWorkspace} from "@/components/DeFiWorkspace";
import {DeFiProvider} from "@/components/DeFiContext";
export default function Demo(){return <DeFiProvider><DeFiWorkspace demoOnly/></DeFiProvider>;}
