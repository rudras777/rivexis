import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,chmodSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,dirname,basename} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

const gate=fileURLToPath(new URL('./npm-audit-ci.mjs',import.meta.url));
const advisory={name:'braces',dependency:'braces',severity:'high',url:'https://github.com/advisories/GHSA-vfj7-8cjw-p6xm',title:'Known build-tool advisory'};
const entry=(name,severity,via)=>({name,severity,via,nodes:[`node_modules/${name}`],effects:[],range:'*',isDirect:false,fixAvailable:false});
function report(vulnerabilities={}){
 const counts={info:0,low:0,moderate:0,high:0,critical:0,total:0};
 for(const value of Object.values(vulnerabilities)){counts[value.severity]++;counts.total++;}
 return {auditReportVersion:2,vulnerabilities,metadata:{vulnerabilities:counts}};
}
const known=()=>report({braces:entry('braces','high',[{...advisory}]),micromatch:entry('micromatch','high',['braces'])});
const formerChain=()=>report({braces:entry('braces','high',[{...advisory}]),micromatch:entry('micromatch','high',['braces']),'fast-glob':entry('fast-glob','high',['micromatch']),'vite-plugin-dynamic-import':entry('vite-plugin-dynamic-import','high',['fast-glob']),'vite-plugin-commonjs':entry('vite-plugin-commonjs','high',['vite-plugin-dynamic-import']),vinext:entry('vinext','high',['vite-plugin-commonjs']),'@vinext/cloudflare':entry('@vinext/cloudflare','high',['vinext'])});
function runAuditFixture({data,raw,status=0}){
 // Run the real CLI gate with an isolated npm executable, without network or lockfile changes.
 const dir=mkdtempSync(join(tmpdir(),'rivexis-audit-gate-'));
 try{
  writeFileSync(join(dir,'fixture.json'),JSON.stringify({raw:raw??JSON.stringify(data),status}));
  writeFileSync(join(dir,'runner.cjs'),`const fs=require('node:fs');const path=require('node:path');const f=JSON.parse(fs.readFileSync(path.join(__dirname,'fixture.json'),'utf8'));process.stdout.write(f.raw);process.exitCode=f.status;`);
  if(process.platform==='win32')writeFileSync(join(dir,'npm.cmd'),`@"${process.execPath}" "%~dp0runner.cjs"\r\n@exit /b %errorlevel%\r\n`);
  else{writeFileSync(join(dir,'npm'),`#!/bin/sh\nexec '${process.execPath.replaceAll("'","'\\''")}' '${join(dir,'runner.cjs').replaceAll("'","'\\''")}'\n`);chmodSync(join(dir,'npm'),0o755);}
  // Windows environment keys are case-insensitive, Node selects the first spelling.
  const env=Object.fromEntries(Object.entries(process.env).filter(([key])=>key.toLowerCase()!=='path'));
  env.PATH=dir+(process.platform==='win32'?';':':')+process.env.PATH;
  const result=spawnSync(process.execPath,[gate],{encoding:'utf8',env,timeout:10000});
  assert.ifError(result.error);
  assert.equal(result.signal,null,'gate must finish normally');
  return result;
 }finally{
  assert.equal(dirname(resolve(dir)),resolve(tmpdir()));
  assert.ok(basename(dir).startsWith('rivexis-audit-gate-'));
  rmSync(dir,{recursive:true,force:true});
 }
}
const scenarios=[
 ['clean valid report',{data:report()},true],
 ['moderate-only report',{data:report({example:entry('example','moderate',[{...advisory,name:'example',severity:'moderate'}])}),status:1},true],
 ['retired advisory must no longer bypass the gate',{data:known(),status:1},false],
 ['entire former seven-package exception must fail',{data:formerChain(),status:1},false],
 ['registry error JSON',{data:{error:{code:'E500',summary:'registry unavailable'}},status:1},false],
 ['error embedded in otherwise valid report',{data:{...report(),error:{code:'EAUDITNOLOCK'}},status:1},false],
 ['unexpected npm exit code with clean JSON',{data:report(),status:2},false],
 ['success exit contradicts reported vulnerabilities',{data:known(),status:0},false],
 ['failure exit contradicts clean report',{data:report(),status:1},false],
 ['empty stdout',{raw:'',status:1},false],
 ['truncated JSON',{raw:'{"auditReportVersion":2',status:1},false],
 ['array instead of report',{data:[],status:0},false],
 ['missing vulnerabilities',{data:{auditReportVersion:2,metadata:{vulnerabilities:{high:0,critical:0,total:0}}}},false],
 ['missing counts',{data:{auditReportVersion:2,vulnerabilities:{}}},false],
 ['unsupported audit schema',{data:{...report(),auditReportVersion:3}},false],
 ['counts hide missing critical entry',{data:{...report(),metadata:{vulnerabilities:{info:0,low:0,moderate:0,high:0,critical:1,total:1}}},status:1},false],
 ['unknown severity',{data:{...report(),vulnerabilities:{braces:entry('braces','unknown',[])}},status:1},false],
 ['unexpected high package',{data:report({other:entry('other','high',[advisory])}),status:1},false],
 ['critical escalation',{data:report({braces:entry('braces','critical',[{...advisory,severity:'critical'}])}),status:1},false],
 ['different advisory',{data:report({braces:entry('braces','high',[{...advisory,url:'https://github.com/advisories/GHSA-other-new-issue'}])}),status:1},false],
 ['advisory ID in untrusted title',{data:report({braces:entry('braces','high',[{...advisory,url:'https://example.invalid/advisory',title:'GHSA-vfj7-8cjw-p6xm'}])}),status:1},false],
 ['unexpected transitive dependency',{data:report({braces:entry('braces','high',[advisory]),vinext:entry('vinext','high',['other'])}),status:1},false],
 ['missing advisory evidence',{data:report({braces:entry('braces','high',[])}),status:1},false],
 ['high advisory hidden under moderate severity',{data:report({braces:entry('braces','moderate',[advisory])}),status:1},false],
 ['critical advisory hidden under high severity',{data:report({braces:entry('braces','high',[{...advisory,severity:'critical'}])}),status:1},false],
 ['critical transitive severity understated',{data:report({braces:entry('braces','critical',[{...advisory,severity:'critical'}]),vinext:entry('vinext','high',['braces'])}),status:1},false],
 ['malformed advisory',{data:report({braces:entry('braces','high',[null])}),status:1},false],
 ['fractional count',{data:{...report(),metadata:{vulnerabilities:{info:0,low:0,moderate:0,high:0.5,critical:0,total:0}}}},false],
 ['renamed package evidence',{data:report({braces:entry('different','high',[advisory])}),status:1},false],
];
for(const [name,fixture,allowed] of scenarios)test(`audit gate: ${name}`,()=>{
 const result=runAuditFixture(fixture);
 assert.equal(result.status,allowed?0:1,`${name}: ${result.stdout}\n${result.stderr}`);
 if(allowed)assert.match(result.stdout+result.stderr,/PASS/);
 else assert.doesNotMatch(result.stdout,/PASS/);
 assert.doesNotMatch(result.stdout+result.stderr,/TEMPORARY EXCEPTION/);
});
