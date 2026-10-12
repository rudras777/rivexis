import {isAddress} from "viem";
// Display/default preferences only. Never use user metadata for authorization.
export const DEFAULT_PREFERENCES=Object.freeze({theme:'dark',motion:'system',contrast:'standard',density:'comfortable',textSize:'standard',numberGrouping:true,healthPrecision:3,timezone:'system',defaultBudget:'3000',defaultTarget:'1.50',defaultFee:'25',defaultObjective:'target',defaultCoverage:'aave',walletAddresses:[],contracts:[]});
const choices={theme:['dark','light','system'],motion:['system','reduce'],contrast:['standard','high'],density:['comfortable','compact'],textSize:['standard','large'],healthPrecision:[3,4,6],timezone:['system','UTC','Asia/Kolkata','Europe/London','America/New_York'],defaultObjective:['target','max-min'],defaultCoverage:['aave','morpho-wbtc','combined']};
function decimal(value,min,max){if(typeof value!=='string'||!/^\d{1,12}(\.\d{1,8})?$/.test(value))throw new Error('Use a nonnegative decimal with at most eight decimal places');const [a,b='']=value.split('.');const raw=BigInt(a)*100000000n+BigInt(b.padEnd(8,'0'));if(raw<min*100000000n||raw>max*100000000n)throw new Error('Preference is outside supported limits');return value;}
export function validatePreferences(input){
 if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Preferences must be an object');
 for(const key of Object.keys(input))if(!Object.hasOwn(DEFAULT_PREFERENCES,key))throw new Error('Unsupported preference');
 const p={...DEFAULT_PREFERENCES,...input};
 for(const [key,allowed] of Object.entries(choices))if(!allowed.includes(p[key]))throw new Error('Unsupported preference value');
 if(typeof p.numberGrouping!=='boolean')throw new Error('Number grouping must be boolean');
 p.defaultBudget=decimal(p.defaultBudget,0n,1000000n);p.defaultFee=decimal(p.defaultFee,0n,10000n);p.defaultTarget=decimal(p.defaultTarget,1n,10n);
 const raw=v=>{const [a,b='']=v.split('.');return BigInt(a)*100000000n+BigInt(b.padEnd(8,'0'))};if(raw(p.defaultFee)>raw(p.defaultBudget))throw new Error('Fee reserve cannot exceed the capital budget');
 if(!Array.isArray(p.walletAddresses)||p.walletAddresses.length>5||p.walletAddresses.some(a=>typeof a!=='string'||!/^0x[\da-fA-F]{40}$/.test(a)))throw new Error('Save up to five valid Ethereum addresses');
 if(!Array.isArray(p.contracts)||p.contracts.length>5||p.contracts.some(c=>!c||typeof c!=='object'||Array.isArray(c)||Object.keys(c).some(k=>!['address','chainId','label'].includes(k))||c.chainId!==1||typeof c.address!=='string'||!isAddress(c.address,{strict:true})||/^0x0{40}$/i.test(c.address)||typeof c.label!=='string'||c.label.length>40||/[\u0000-\u001f\u007f]/.test(c.label)))throw new Error('Save up to five Ethereum contract identities with short labels');
 p.contracts=p.contracts.map(c=>({...c,address:c.address.toLowerCase(),label:c.label.trim()}));if(new Set(p.contracts.map(c=>c.address)).size!==p.contracts.length)throw new Error('Contract identities must be unique');
 p.walletAddresses=[...new Set(p.walletAddresses.map(a=>a.toLowerCase()))];return p;
}
export function storedPreferences(value){try{return validatePreferences(value??{})}catch{return {...DEFAULT_PREFERENCES,walletAddresses:[]}}}
export function validateAccountUpdate(input){if(!input||typeof input!=='object'||Array.isArray(input)||Object.keys(input).some(k=>!['displayName','preferences'].includes(k)))throw new Error('Unsupported account update');if(typeof input.displayName!=='string'||input.displayName.trim().length>60||/[\u0000-\u001f\u007f]/.test(input.displayName))throw new Error('Display name must contain at most 60 characters');return {displayName:input.displayName.trim(),preferences:validatePreferences(input.preferences)};}
