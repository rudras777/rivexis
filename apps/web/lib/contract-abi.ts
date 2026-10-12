import {parseAbi,type AbiFunction} from 'viem';
export const metadataFunctions=parseAbi(['function name() view returns (string)','function symbol() view returns (string)','function decimals() view returns (uint8)','function totalSupply() view returns (uint256)']) as readonly AbiFunction[];
function scalar(type:unknown){if(typeof type!=='string')return false;if(['address','bool','string','bytes'].includes(type))return true;const bytes=/^bytes(\d+)$/.exec(type);if(bytes)return Number(bytes[1])>=1&&Number(bytes[1])<=32;const number=/^(?:u?int)(\d*)$/.exec(type);return !!number&&(!number[1]||(Number(number[1])>=8&&Number(number[1])<=256&&Number(number[1])%8===0))}
export function contractReadFunctions(text:string):readonly AbiFunction[]{
 if(!text.trim())return metadataFunctions;
 if(new TextEncoder().encode(text).length>16384)throw Error('ABI must contain at most 16 KB.');
 let value:unknown;try{value=JSON.parse(text)}catch{throw Error('Enter a valid JSON ABI array.')}
 if(!Array.isArray(value)||value.length>64)throw Error('ABI must be an array with at most 64 entries.');
 const functions:AbiFunction[]=[];
 for(const item of value){if(!item||typeof item!=='object'||typeof item.type!=='string')throw Error('ABI entries require an explicit type.');if(item.type!=='function')continue;
  if(typeof item.name!=='string'||!/^[$A-Za-z_]\w{0,63}$/.test(item.name)||!Array.isArray(item.inputs)||!Array.isArray(item.outputs)||!['view','pure','payable','nonpayable'].includes(item.stateMutability))throw Error('Function ABI requires a name, inputs, outputs and state mutability.');
  if(['view','pure'].includes(item.stateMutability)&&item.inputs.length===0&&item.outputs.length>0&&item.outputs.length<=8&&item.outputs.every((p:unknown)=>!!p&&typeof p==='object'&&scalar((p as {type:unknown}).type)))functions.push(item as AbiFunction);
 }
 if(new Set(functions.map(f=>f.name)).size!==functions.length)throw Error('Zero-argument read function names must be unique.');
 return functions;
}
