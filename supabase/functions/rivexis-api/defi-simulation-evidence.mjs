// Shared provider-envelope checks; neither caller accepts client calldata or overrides.
export const simulationQuantity=v=>'0x'+BigInt(v).toString(16);
export const validSimulationQuantity=v=>typeof v==='string'&&/^0x(?:0|[1-9a-f][0-9a-f]*)$/i.test(v);
export const validSimulationHash=v=>typeof v==='string'&&/^0x[0-9a-f]{64}$/i.test(v);
export function simulationBlock(result,prepared,parent){
 if(!Array.isArray(result)||result.length!==1)throw new Error('Incomplete sequence block');const b=result[0];
 if(!validSimulationHash(b.parentHash)||b.parentHash.toLowerCase()!==parent.hash.toLowerCase()||!validSimulationQuantity(b.number)||BigInt(b.number)!==BigInt(parent.number)+1n||!validSimulationQuantity(b.timestamp)||BigInt(b.timestamp)!==BigInt(parent.timestamp)+12n||!validSimulationQuantity(b.baseFeePerGas)||BigInt(b.baseFeePerGas)<=0n||!Array.isArray(b.calls)||b.calls.length!==prepared.calls.length)throw new Error('Invalid sequence parent or call evidence');
 for(let i=0;i<b.calls.length;i++){const c=b.calls[i];if(!['0x0','0x1'].includes(c.status)||!validSimulationQuantity(c.gasUsed)||BigInt(c.gasUsed)<=0n||BigInt(c.gasUsed)>BigInt(prepared.calls[i].call.gas)||typeof c.returnData!=='string'||!/^0x(?:[0-9a-f]{2})*$/i.test(c.returnData))throw new Error('Invalid sequence result evidence')}
 return b;
}
