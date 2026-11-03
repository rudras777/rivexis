import {spawnSync} from 'node:child_process';

// npm supplies its own CLI path on every supported platform. Avoid shell quoting
// and prevent an ordinary local preview from forwarding requests to production.
const npmCli=process.env.npm_execpath;
if(!npmCli)throw new Error('Start the safe local preview with npm run dev:web');
console.log('Local preview: use localhost at the port shown below. Production API forwarding is disabled; authenticated workflow tests use isolated fixtures.');
const result=spawnSync(process.execPath,[npmCli,'--workspace','@rivexis/web','run','dev','--','--hostname','127.0.0.1',...process.argv.slice(2)],{
 stdio:'inherit',windowsHide:true,
 env:{...process.env,NEXT_PUBLIC_RIVEXIS_API_URL:'same-origin',RIVEXIS_E2E_BLOCK_EXTERNAL_UPSTREAM:'1'},
});
if(result.error)throw result.error;
process.exit(result.status??1);
