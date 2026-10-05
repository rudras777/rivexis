import {spawnSync} from "node:child_process";

const npmCommand=process.platform==="win32"?"npm.cmd":"npm";
const isWorkersBuild=process.env.WORKERS_CI==="1";
const script=isWorkersBuild?"build:vinext":"build:next";

const result=spawnSync(npmCommand,["run",script],{
  stdio:"inherit",
  env:process.env,
});

if(result.error)throw result.error;
process.exit(result.status??1);
