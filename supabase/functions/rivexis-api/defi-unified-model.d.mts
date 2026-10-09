import type {Snapshot,Position,Action,Metrics,Frontier} from './defi-model.mjs';
export type {Snapshot,Position,Action,Metrics,Frontier,Reserve,Alternative} from './defi-model.mjs';
export {format} from './defi-model.mjs';
export const MODEL:string;
export function validateSnapshot(snapshot:Snapshot,now?:number):Snapshot;
export function metrics(position:Position,shocks?:Record<string,number>,actions?:Action[]):Metrics;
export function scenario(snapshot:Snapshot,shocks?:Record<string,number>,actions?:Action[],now?:number):Metrics[];
export function frontier(snapshot:Snapshot,input:{budget:string;target?:string;gasReserve?:string;shocks?:Record<string,number>;objective?:string},now?:number):Frontier;
