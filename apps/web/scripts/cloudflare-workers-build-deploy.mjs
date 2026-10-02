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
const packageRoot=fileURLToPath(new URL("..",import.meta.url));
const env={
  ...process.env,
  CLOUDFLARE_ACCOUNT_ID:process.env.CLOUDFLARE_ACCOUNT_ID||"0b22778ba197266a58dd26eeef0334a8",
  NEXT_PUBLIC_RIVEXIS_API_URL:"same-origin",
  NEXT_PUBLIC_RIVEXIS_BUILD_SHA:commitSha,
};

const result=spawnSync(npmCommand,["run","deploy:vinext"],{
  cwd:packageRoot,
  stdio:"inherit",
  env,
});
if(result.error)throw result.error;
process.exit(result.status??1);
