import {spawnSync} from "node:child_process";

const commitSha=(process.env.WORKERS_CI_COMMIT_SHA||"").trim();
if(!/^[0-9a-f]{40}$/i.test(commitSha)){
  throw new Error("WORKERS_CI_COMMIT_SHA must be the exact 40-character Git commit SHA supplied by Cloudflare Workers Builds.");
}

if(process.env.WORKERS_CI!=="1"){
  throw new Error("This deployment entrypoint is reserved for Cloudflare Workers Builds. Use the existing authenticated deploy workflow for other environments.");
}

const command=process.platform==="win32"?"npm.cmd":"npm";
const result=spawnSync(command,["--workspace","@rivexis/web","run","deploy:vinext"],{
  stdio:"inherit",
  env:{
    ...process.env,
    NEXT_PUBLIC_RIVEXIS_API_URL:"same-origin",
    NEXT_PUBLIC_RIVEXIS_BUILD_SHA:commitSha,
  },
});

if(result.error)throw result.error;
process.exit(result.status??1);
