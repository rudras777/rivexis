export type NavigationEvidence={browserName:string;expectedOrigin:string;target:string;href:string;previousHref:string;previousTimeOrigin:number;timeOrigin:number;readyState:string;contentPresent:boolean;buildPresent:boolean;documentStatus:number;pending:number;pageErrors:number;resourceFailures:number;serverFailures:number};
export function mayReleaseStrandedNavigation(e:NavigationEvidence):boolean;
export function runGuardedNavigation<T>(callbacks:{initial:()=>Promise<T>;inspect:()=>Promise<NavigationEvidence|null>;release:()=>Promise<T>;record:(e:NavigationEvidence)=>void}):Promise<T>;
