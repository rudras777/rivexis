import {spawnSync} from "node:child_process";

const commitSha=(process.env.WORKERS_CI_COMMIT_SHA||"").trim();
const isWorkersBuild=process.env.WORKERS_CI==="1";

if(isWorkersBuild && !/^[0-9a-f]{40}$/i.test(commitSha)){
  throw new Error("WORKERS_CI_COMMIT_SHA must be the exact 40-character Git commit SHA supplied by Cloudflare Workers Builds.");
}

const npmCommand=process.platform==="win32"?"npm.cmd":"npm";
const env={
  ...process.env,
  NEXT_PUBLIC_RIVEXIS_API_URL:process.env.NEXT_PUBLIC_RIVEXIS_API_URL||"same-origin",
  NEXT_PUBLIC_RIVEXIS_BUILD_SHA:isWorkersBuild?commitSha:(process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA||"development"),
};

const result=spawnSync(npmCommand,["--workspace","@rivexis/web","run","build:vinext"],{
  stdio:"inherit",
  env,
  shell:process.platform==="win32",
});
if(result.error)throw result.error;
process.exit(result.status??1);
