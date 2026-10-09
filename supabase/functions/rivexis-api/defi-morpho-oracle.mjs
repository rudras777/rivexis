// Staging-only, pinned Ethereum WBTC/USDC market. No generic oracle fallback.
// V1 ChainlinkOracle source: morpho-blue-oracles@6941f06e411ca17c692fc63824cc60eeeec0035e.
export const MORPHO_WBTC = Object.freeze({
  marketId:'0x3a85e619751152991742810df6ec69ce473daef99e28a64ab2340d7b7ccfee49',
  loanToken:'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
  collateralToken:'0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
  oracle:'0xdddd770badd886df3864029e4b377b5f6a2b6b83',
  codeHash:'0x726b2513a5e9cc64d93af23e2fba053db6f6801132e56d4b6b7882a66b239dc9',
  irm:'0x870ac11d48b15db9a138cf899d20f13f79ba00bc',
  lltvRaw:'860000000000000000',
  feeds:Object.freeze([
    Object.freeze({kind:'WBTC_BTC',address:'0xfdfd9c85ad200c506cf9e21f1fd8dd01932fbb23',maxAge:90000}),
    Object.freeze({kind:'BTC_USD',address:'0xf4030086522a5beea4988f8ca5b36dbc97bee88c',maxAge:4200}),
    Object.freeze({kind:'USDC_USD',address:'0x8fffffd4afb6115b954bd326cbe7b4ba576818f6',maxAge:90000}),
  ]),
});
const zero='0x0000000000000000000000000000000000000000',max=2n**256n;
const same=(a,b)=>typeof a==='string'&&a.toLowerCase()===b;
function fresh(round,timestamp,age){
  return Array.isArray(round)&&round.length===5&&round.every(x=>typeof x==='bigint'&&x>=0n&&x<max)&&
    round[0]>0n&&round[4]>=round[0]&&round[1]>0n&&round[2]>0n&&round[2]<=round[3]&&round[3]<=timestamp&&timestamp-round[3]<=BigInt(age);
}
export function validateMorphoWbtcOracle(e){
  if(!e||!same(e.marketId,MORPHO_WBTC.marketId)||!same(e.oracle,MORPHO_WBTC.oracle)||
    e.codeHash!==MORPHO_WBTC.codeHash||!same(e.loanToken,MORPHO_WBTC.loanToken)||
    !same(e.collateralToken,MORPHO_WBTC.collateralToken)||!same(e.irm,MORPHO_WBTC.irm)||
    e.lltvRaw!==MORPHO_WBTC.lltvRaw||!same(e.vault,zero)||e.vaultConversionSample!==1n||
    !same(e.quoteFeed2,zero)||e.scaleFactor!==10n**26n||e.loanDecimals!==6||e.collateralDecimals!==8||
    typeof e.blockTimestamp!=='bigint'||e.blockTimestamp<=0n||e.blockTimestamp>=max||
    typeof e.price!=='bigint'||e.price<=0n||e.price>=max||!Array.isArray(e.feeds)||e.feeds.length!==3)return false;
  if(!e.feeds.every((f,i)=>same(f?.address,MORPHO_WBTC.feeds[i].address)&&f.decimals===8&&fresh(f.round,e.blockTimestamp,MORPHO_WBTC.feeds[i].maxAge)))return false;
  // V1 uses full-precision mulDiv(scaleFactor, base1*base2, quote1).
  // Check intermediate products and quotient against its Solidity bounds.
  const base=e.feeds[0].round[1]*e.feeds[1].round[1];if(base>=max)return false;
  const price=e.scaleFactor*base/e.feeds[2].round[1];return price<max&&price===e.price;
}
