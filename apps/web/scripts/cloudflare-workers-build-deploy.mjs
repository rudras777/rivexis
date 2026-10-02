import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const commitSha=(process.env.WORKERS_CI_COMMIT_SHA||"").trim();
if(!/^[0-9a-f]{40}$/i.test(commitSha)){
  throw new Error("WORKERS_CI_COMMIT_SHA must be the exact 40-character Git commit SHA supplied by Cloudflare Workers Builds.");
}

if(process.env.WORKERS_CI!=="1"){
  throw new Error("This deployment entrypoint is reserved for Cloudflare Workers Builds. Use the existing authenticated deploy workflow for other environments.");
}

const npmCommand=process.platform==="win32"?"npm.cmd":"npm";
const npxCommand=process.platform==="win32"?"npx.cmd":"npx";
const packageRoot=fileURLToPath(new URL("..",import.meta.url));
const env={
  ...process.env,
  NEXT_PUBLIC_RIVEXIS_API_URL:"same-origin",
  NEXT_PUBLIC_RIVEXIS_BUILD_SHA:commitSha,
};

function run(command,args){
  const result=spawnSync(command,args,{cwd:packageRoot,stdio:"inherit",env});
  if(result.error)throw result.error;
  if((result.status??1)!==0)process.exit(result.status??1);
}

run(npmCommand,["run","build:vinext"]);
run(npxCommand,["wrangler","deploy","--config","dist/server/wrangler.json"]);
