import {spawnSync} from "node:child_process";

const SEVERE=new Set(["high","critical"]);
const LEVELS=["info","low","moderate","high","critical"];
const isRecord=value=>value!==null&&typeof value==="object"&&!Array.isArray(value);
function fail(message){console.error(`npm audit gate: FAIL (${message})`);process.exit(1)}

const command=process.platform==="win32"?"npm.cmd":"npm";
const audit=spawnSync(command,["audit","--json","--audit-level=info"],{encoding:"utf8",timeout:60000,maxBuffer:16*1024*1024,shell:process.platform==="win32"});
if(audit.error){
  console.error(`npm audit could not run: ${audit.error.message}`);
  process.exit(1);
}
if(!audit.stdout?.trim()){
  console.error("npm audit returned no JSON report; refusing to bypass the security gate.");
  if(audit.stderr)console.error(audit.stderr.trim());
  process.exit(1);
}
if(audit.signal||![0,1].includes(audit.status))fail("audit process did not complete normally");

let report;
try{report=JSON.parse(audit.stdout)}catch(error){
  console.error("npm audit returned malformed JSON; refusing to bypass the security gate.");
  console.error(error instanceof Error?error.message:String(error));
  process.exit(1);
}

// Registry/CLI errors can be valid JSON. Missing evidence must never mean a clean audit.
if(!isRecord(report)||report.auditReportVersion!==2||report.error!==undefined)fail("unsupported, malformed or error audit report");
const vulnerabilities=report.vulnerabilities;
const counts=report.metadata?.vulnerabilities;
if(!isRecord(vulnerabilities)||!isRecord(counts))fail("missing audit findings or summary");
if([...LEVELS,"total"].some(level=>!Number.isSafeInteger(counts[level])||counts[level]<0))fail("invalid audit counts");
const actual=Object.fromEntries(LEVELS.map(level=>[level,0]));
for(const [name,value] of Object.entries(vulnerabilities)){
  if(!isRecord(value)||value.name!==name||!LEVELS.includes(value.severity)||!Array.isArray(value.via)||value.via.length===0)fail("malformed vulnerability evidence");
  for(const via of value.via){
    if(typeof via==="string"){
      if(!isRecord(vulnerabilities[via]))fail("missing transitive vulnerability evidence");
    }else if(!isRecord(via)||!LEVELS.includes(via.severity)||typeof via.name!=="string"||typeof via.url!=="string")fail("malformed advisory evidence");
    const dependencySeverity=typeof via==="string"?vulnerabilities[via].severity:via.severity;
    if(LEVELS.indexOf(dependencySeverity)>LEVELS.indexOf(value.severity))fail("package severity understates advisory evidence");
  }
  actual[value.severity]++;
}
const total=Object.keys(vulnerabilities).length;
if(counts.total!==total||LEVELS.some(level=>actual[level]!==counts[level]))fail("audit findings contradict their summary");
if(audit.status!==(total>0?1:0))fail("audit exit status contradicts findings");
const severe=Object.entries(vulnerabilities).filter(([,value])=>SEVERE.has(value?.severity));
if(severe.length===0){
  console.log("npm audit gate: PASS (no high or critical vulnerabilities)");
  process.exit(0);
}

// The former Braces advisory was withdrawn. Retain evidence validation above,
// but no package, dependency chain or advisory may bypass this severity gate.
console.error("npm audit gate: FAIL (high or critical vulnerabilities are not excepted)");
for(const [name,value] of severe)console.error(`- ${name}: ${value.severity}`);
process.exit(1);
