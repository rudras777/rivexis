import {spawnSync} from "node:child_process";

const npmCommand=process.platform==="win32"?"npm.cmd":"npm";
const isWorkersBuild=process.env.WORKERS_CI==="1";
const commitSha=(process.env.WORKERS_CI_COMMIT_SHA||"").trim();

if(isWorkersBuild&&!/^[0-9a-f]{40}$/i.test(commitSha)){
  throw new Error("WORKERS_CI_COMMIT_SHA must be the exact 40-character Git commit SHA supplied by Cloudflare Workers Builds.");
}

const script=isWorkersBuild?"build:vinext":"build:next";
const env={
  ...process.env,
  NEXT_PUBLIC_RIVEXIS_API_URL:isWorkersBuild?"same-origin":process.env.NEXT_PUBLIC_RIVEXIS_API_URL,
  NEXT_PUBLIC_RIVEXIS_BUILD_SHA:isWorkersBuild?commitSha:process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA,
};

const result=spawnSync(npmCommand,["run",script],{
  stdio:"inherit",
  env,
  shell:process.platform==="win32",
});

if(result.error)throw result.error;
process.exit(result.status??1);
