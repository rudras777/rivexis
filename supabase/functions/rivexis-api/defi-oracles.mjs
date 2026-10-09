// Validated WBTC composite adapter. Identity and both timestamped component
// feeds are required; the adapter itself has no latestRoundData interface.
export const WBTC_ORACLE = Object.freeze({
  asset:'0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
  source:'0xdaa4b74c6bac4e25188e64ebc68db5050b690cac',
  codeHash:'0x585d9bff94e70a45a18e9f7b03dcb249051e32a6cba0f14c6ab81e194595364e',
  baseFeed:'0xb41e773f507f7a7ea890b1afb7d2b660c30c8b0a',
  ratioFeed:'0xfdfd9c85ad200c506cf9e21f1fd8dd01932fbb23',
  // Explicit beta freshness bounds, not a promise about feed update timing.
  baseMaxAge:4200, ratioMaxAge:90000,
});
function fresh(round, timestamp, maxAge){
  return Array.isArray(round)&&round.length===5&&round.every(v=>typeof v==='bigint')&&
    round[0]>0n&&round[4]>=round[0]&&round[1]>0n&&round[2]>0n&&round[2]<=round[3]&&
    round[3]>0n&&round[3]<=timestamp&&timestamp-round[3]<=BigInt(maxAge);
}
export function validateWbtcOracle(evidence){
  const {source,codeHash,baseFeed,ratioFeed,baseDecimals,ratioDecimals,decimals,denominator,baseRound,ratioRound,price,blockTimestamp}=evidence;
  const identity=source?.toLowerCase()===WBTC_ORACLE.source&&codeHash===WBTC_ORACLE.codeHash&&
    baseFeed?.toLowerCase()===WBTC_ORACLE.baseFeed&&ratioFeed?.toLowerCase()===WBTC_ORACLE.ratioFeed;
  const units=baseDecimals===8&&ratioDecimals===8&&decimals===8&&denominator===10n**16n;
  const timestamps=typeof blockTimestamp==='bigint'&&fresh(baseRound,blockTimestamp,WBTC_ORACLE.baseMaxAge)&&fresh(ratioRound,blockTimestamp,WBTC_ORACLE.ratioMaxAge);
  const formula=Boolean(timestamps&&units&&typeof price==='bigint'&&price>0n&&baseRound[1]*ratioRound[1]*10n**8n/denominator===price);
  return Boolean(identity&&units&&timestamps&&formula);
}
