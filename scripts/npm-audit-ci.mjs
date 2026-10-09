import {spawnSync} from "node:child_process";

const ADVISORY_ID="GHSA-vfj7-8cjw-p6xm";
const ALLOWED_CHAIN=new Set([
  "braces",
  "micromatch",
  "fast-glob",
  "vite-plugin-dynamic-import",
  "vite-plugin-commonjs",
  "vinext",
  "@vinext/cloudflare",
]);
const SEVERE=new Set(["high","critical"]);

const command=process.platform==="win32"?"npm.cmd":"npm";
const audit=spawnSync(command,["audit","--json"],{encoding:"utf8",maxBuffer:16*1024*1024,shell:process.platform==="win32"});
if(audit.error){
  console.error(`npm audit could not run: ${audit.error.message}`);
  process.exit(1);
}
if(!audit.stdout?.trim()){
  console.error("npm audit returned no JSON report; refusing to bypass the security gate.");
  if(audit.stderr)console.error(audit.stderr.trim());
  process.exit(1);
}

let report;
try{report=JSON.parse(audit.stdout)}catch(error){
  console.error("npm audit returned malformed JSON; refusing to bypass the security gate.");
  console.error(error instanceof Error?error.message:String(error));
  process.exit(1);
}

const vulnerabilities=report.vulnerabilities??{};
const severe=Object.entries(vulnerabilities).filter(([,value])=>SEVERE.has(value?.severity));
if(severe.length===0){
  console.log("npm audit gate: PASS (no high or critical vulnerabilities)");
  process.exit(0);
}

const unexpected=[];
let expectedDirectAdvisory=false;
for(const [name,value] of severe){
  if(!ALLOWED_CHAIN.has(name)){
    unexpected.push(`${name}: unexpected ${value?.severity??"unknown"} vulnerability`);
    continue;
  }
  if(value?.severity==="critical"){
    unexpected.push(`${name}: critical severity is never excepted`);
  }
  for(const via of value?.via??[]){
    if(typeof via==="string"){
      if(!ALLOWED_CHAIN.has(via))unexpected.push(`${name}: unexpected vulnerable dependency ${via}`);
      continue;
    }
    if(!via||!SEVERE.has(via.severity))continue;
    const marker=`${via.url??""} ${via.title??""} ${via.name??""}`;
    if(marker.includes(ADVISORY_ID)){
      if(name==="braces")expectedDirectAdvisory=true;
    }else{
      unexpected.push(`${name}: unexpected advisory ${via.url??via.title??via.source??"unknown"}`);
    }
  }
}

if(!expectedDirectAdvisory){
  unexpected.push(`expected direct advisory ${ADVISORY_ID} was not present on braces`);
}

if(unexpected.length){
  console.error("npm audit gate: FAIL");
  for(const item of unexpected)console.error(`- ${item}`);
  process.exit(1);
}

console.warn(
  `npm audit gate: TEMPORARY EXCEPTION for ${ADVISORY_ID} only. `+
  "The advisory currently has no patched braces release and is reached through the Vinext build-tool chain. " +
  "Any different high/critical advisory still fails CI."
);
process.exit(0);
