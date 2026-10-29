import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const script=fileURLToPath(new URL('./check-deploy-env.mjs',import.meta.url));
function check(origin){
  return spawnSync(process.execPath,[script],{
    env:{...process.env,NEXT_PUBLIC_RIVEXIS_API_URL:'same-origin',NEXT_PUBLIC_RIVEXIS_PUBLIC_WEB_URL:origin},
    encoding:'utf8',
  });
}

for(const origin of ['', 'https://rivexis-web.rudrasingh0718.workers.dev','https://rivexis.rvea.info'])test(`deployment accepts the approved canonical setting ${origin||'(legacy default)'}`,()=>{
  assert.equal(check(origin).status,0);
});

for(const origin of ['https://untrusted.example','http://rivexis.rvea.info','https://rivexis.rvea.info.untrusted.example','https://rivexis.rvea.info/','https://rivexis.rvea.info?redirect=untrusted'])test(`deployment rejects unapproved canonical setting ${origin}`,()=>{
  const result=check(origin);
  assert.notEqual(result.status,0);
  assert.match(result.stderr,/exact approved RIVEXIS production origin/);
});
