import {writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export const accountId='0b22778ba197266a58dd26eeef0334a8';
const projectName='rvea-rivexis-gateway',workerName='rivexis-web',hostname='rivexis.rvea.info';
const apiRoot=`https://api.cloudflare.com/client/v4/accounts/${accountId}`;

// These are deliberately fixed GET targets. Never persist complete provider responses:
// Pages configuration includes environment-variable values and analytics credentials.
export async function auditCloudflare({pagesToken,workerToken,fetcher=fetch,now=()=>new Date()}){
  if(![pagesToken,workerToken].every(token=>typeof token==='string'&&/^[A-Za-z0-9_-]{40,}$/.test(token)))throw new Error('Both existing raw deployment tokens are required');
  async function read(path,token){
    let response;
    try{response=await fetcher(apiRoot+path,{method:'GET',redirect:'error',headers:{Authorization:`Bearer ${token}`},signal:AbortSignal.timeout(20000)})}
    catch{throw new Error('Cloudflare read transport failed')}
    let body;
    try{body=await response.json()}catch{throw new Error(`Cloudflare read returned non-JSON (HTTP ${response.status})`)}
    if(!response.ok||body.success!==true){
      const codes=(body.errors??[]).map(error=>error.code).filter(code=>Number.isSafeInteger(code)).join(',')||'unavailable';
      throw new Error(`Cloudflare read failed (HTTP ${response.status}; codes ${codes})`);
    }
    return body.result;
  }
  const [project,domains,worker]=await Promise.all([
    read(`/pages/projects/${projectName}`,pagesToken),
    read(`/pages/projects/${projectName}/domains`,pagesToken),
    read(`/workers/scripts/${workerName}/deployments`,workerToken),
  ]);
  const production=project?.deployment_configs?.production,preview=project?.deployment_configs?.preview;
  const domain=Array.isArray(domains)?domains.find(item=>item.name===hostname):null;
  const deployment=worker?.deployments?.[0];
  const binding=config=>{
    const value=config?.services?.RIVEXIS_WEB;
    return {service:value?.service??null,environment:value?.environment??null};
  };
  const expectedBinding=config=>config?.services?.RIVEXIS_WEB?.service===workerName&&['production',''].includes(config.services.RIVEXIS_WEB.environment??'');
  const versions=Array.isArray(deployment?.versions)?deployment.versions.map(value=>({version_id:value.version_id,percentage:value.percentage})):[];
  const checks={
    existingProject:project?.name===projectName,
    mainProductionBranch:project?.production_branch==='main',
    productionBinding:expectedBinding(production),
    previewBinding:expectedBinding(preview),
    failClosed:production?.fail_open===false,
    activeCustomDomain:domain?.status==='active',
    activeWorkerDeployment:typeof deployment?.id==='string'&&versions.length>0&&versions.every(value=>typeof value.version_id==='string'&&Number.isFinite(value.percentage)&&value.percentage>0)&&Math.abs(versions.reduce((total,value)=>total+value.percentage,0)-100)<0.001,
  };
  return {
    observed_at:now().toISOString(),account_id:accountId,mode:'read-only',
    pages:{name:project?.name??null,production_branch:project?.production_branch??null,production_deployment_id:project?.canonical_deployment?.id??null,gateway_commit:project?.canonical_deployment?.deployment_trigger?.metadata?.commit_hash??null,production_binding:binding(production),preview_binding:binding(preview),fail_open:production?.fail_open??null,compatibility_date:production?.compatibility_date??null},
    custom_domain:{name:hostname,status:domain?.status??null,certificate_authority:domain?.certificate_authority??null},
    worker:{name:workerName,deployment_id:deployment?.id??null,created_on:deployment?.created_on??null,versions},
    checks,passed:Object.values(checks).every(Boolean),
  };
}

if(process.argv[1]&&fileURLToPath(import.meta.url)===resolve(process.argv[1])){
  try{
    const report=await auditCloudflare({pagesToken:process.env.CLOUDFLARE_PAGES_API_TOKEN,workerToken:process.env.CLOUDFLARE_API_TOKEN});
    await writeFile(resolve(process.argv[2]??'rvea-cloudflare-audit.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report,null,2));
    if(!report.passed)process.exitCode=1;
  }catch(error){console.error(error.message);process.exitCode=1}
}
