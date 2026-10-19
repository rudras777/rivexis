// A test-driver workaround, never application behavior or an assertion waiver.
export function mayReleaseStrandedNavigation(e){
  try{
    const target=new URL(e.target),actual=new URL(e.href);
    const readRoutes=new Set(['/', '/app', '/workspace', '/workspace/overview', '/workspace/wallets', '/workspace/contracts', '/workspace/networks', '/workspace/scenarios', '/workspace/transactions', '/workspace/frontier', '/workspace/reports', '/workspace/history', '/workspace/settings', '/workspace/settings/workspaces', '/workspace/alerts', '/workspace/monitors', '/workspace/decisions', '/workspace/saved', '/workspace/protocol-history', '/workspace/investigations', '/workspace/providers', '/login', '/signup', '/methodology', '/security', '/platform', '/docs', '/about']);
    return e.browserName==='firefox'&&['http:','https:'].includes(target.protocol)
      &&target.origin===e.expectedOrigin&&readRoutes.has(target.pathname)
      &&!target.search&&!target.hash&&target.href===actual.href
      &&e.readyState==='complete'&&e.contentPresent===true&&e.buildPresent===true
      &&(e.previousHref!==e.href||e.previousTimeOrigin!==e.timeOrigin)
      &&Number.isFinite(e.timeOrigin)&&e.timeOrigin>0
      &&Number.isInteger(e.documentStatus)&&e.documentStatus>=200&&e.documentStatus<300
      &&e.pending===0&&e.pageErrors===0&&e.resourceFailures===0&&e.serverFailures===0;
  }catch{return false}
}

// The second GET is bounded and cannot recursively retry. Real errors propagate.
export async function runGuardedNavigation({initial,inspect,release,record}){
  try{return await initial()}
  catch(error){
    if(!(error instanceof Error)||error.name!=='TimeoutError')throw error;
    const evidence=await inspect();
    if(!evidence||!mayReleaseStrandedNavigation(evidence))throw error;
    record(evidence);
    return await release();
  }
}
