export type Preferences={theme:'dark'|'light'|'system';motion:'system'|'reduce';contrast:'standard'|'high';density:'comfortable'|'compact';textSize:'standard'|'large';numberGrouping:boolean;healthPrecision:3|4|6;timezone:'system'|'UTC'|'Asia/Kolkata'|'Europe/London'|'America/New_York';defaultBudget:string;defaultTarget:string;defaultFee:string;defaultObjective:'target'|'max-min';defaultCoverage:'aave'|'morpho-wbtc'|'combined';walletAddresses:string[]};
export const DEFAULT_PREFERENCES:Preferences;
export function validatePreferences(input:unknown):Preferences;
export function storedPreferences(input:unknown):Preferences;
export function validateAccountUpdate(input:unknown):{displayName:string;preferences:Preferences};
