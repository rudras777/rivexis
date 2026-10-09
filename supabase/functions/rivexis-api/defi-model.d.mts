export const MODEL:string;
export const WAD:bigint;
export const USD:bigint;
export interface Reserve {asset:string;symbol:string;decimals:number;collateralRaw:string;debtRaw:string;walletRaw:string;priceRaw:string;ltBps:string;allowanceRaw:string;collateralEnabled:boolean;supplyAllowed:boolean;oracleState:string;isolation:boolean;[key:string]:unknown}
export interface Position {id:string;protocol:string;chainId:number;eMode:number;reserves:Reserve[];[key:string]:unknown}
export interface Snapshot {model:string;status:string;blockTimestamp:number;blockNumber:string;blockHash:string;wallet:string;positions:Position[];warnings:string[];nativeBalanceRaw:string;observedHealthFactorRaw:string|null;[key:string]:unknown}
export interface Action {positionId:string;asset:string;kind:string;amountRaw:string;sharesRaw?:string;symbol?:string;decimals?:number;approvalRequired?:boolean}
export interface Metrics {collateralRaw:string;debtRaw:string;adjustedRaw:string;healthFactorRaw:string|null;liquidatable:boolean;positionId?:string}
export interface Alternative {actions:Action[];capitalRaw:string;totalBudgetRaw:string;feeReserveRaw:string;outcomes:Metrics[];minHealthFactorRaw:string|null;meetsTarget:boolean;uncovered:number;feasibility:string;execution:string}
export interface Frontier {model:string;optimizer:string;objective:string;budgetRaw:string;targetRaw:string;feeReserveRaw:string;gasConstraint:string;baseline:Metrics[];examined:number;meetsTarget:boolean;alternatives:Alternative[];method:string;warnings:string[]}
export function integer(value:string,name?:string):bigint;
export function decimal(value:string,decimals?:number):bigint;
export function format(value:string|bigint,decimals?:number,places?:number):string;
export function validateSnapshot(snapshot:Snapshot,now?:number):Snapshot;
export function metrics(position:Position,shocks?:Record<string,number>,actions?:Action[]):Metrics;
export function scenario(snapshot:Snapshot,shocks?:Record<string,number>,actions?:Action[],now?:number):Metrics[];
export function frontier(snapshot:Snapshot,input:{budget:string;target?:string;gasReserve?:string;shocks?:Record<string,number>;objective?:string},now?:number):Frontier;
