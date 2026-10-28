import {spawn,spawnSync} from 'node:child_process';
import {once} from 'node:events';
import {createServer} from 'node:net';
import {fileURLToPath} from 'node:url';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {BASE_SECURITY_HEADERS} from '../lib/security-headers.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const vinext=fileURLToPath(new URL('./cli.js',import.meta.resolve('vinext')));
const wrangler=fileURLToPath(new URL('../bin/wrangler.js',import.meta.resolve('wrangler')));
const config=path.join(root,'dist/server/wrangler.json');
const asset=path.join(root,'dist/client/_rivexis-public/landing.html');
const result=spawnSync(process.execPath,[vinext,'build'],{cwd:root,stdio:'inherit',env:process.env,windowsHide:true});
if(result.error)throw result.error;
if(result.status!==0)process.exit(result.status??1);
const output=JSON.parse(await fs.readFile(config,'utf8'));
if(output.vars?.RIVEXIS_BUILD_RENDER!==undefined)throw new Error('The local build-render flag must never be deployed');

const reservation=createServer();reservation.listen(0,'127.0.0.1');await once(reservation,'listening');
const port=reservation.address().port;await new Promise(resolve=>reservation.close(resolve));
const child=spawn(process.execPath,[wrangler,'dev','--config',config,'--local','--ip','127.0.0.1','--port',String(port),'--inspector-port','0','--var','RIVEXIS_BUILD_RENDER:1','--show-interactive-dev-session=false','--log-level','error'],{
 cwd:root,stdio:['ignore','pipe','pipe'],windowsHide:true,detached:process.platform!=='win32',env:{...process.env,WRANGLER_SEND_METRICS:'false',CI:'true'},
});
let diagnostics='';let childError;const capture=data=>{diagnostics=(diagnostics+data.toString()).slice(-16000)};
child.stdout.on('data',capture);child.stderr.on('data',capture);child.on('error',error=>{childError=error});
try{
 let response;const deadline=Date.now()+45_000;
 while(Date.now()<deadline){
  if(childError)throw childError;
  if(child.exitCode!==null)throw new Error('Local Worker exited before document generation');
  try{response=await fetch(`http://127.0.0.1:${port}/`,{headers:{accept:'text/html'},signal:AbortSignal.timeout(2500)});break}catch{}
  await new Promise(resolve=>setTimeout(resolve,250));
 }
 if(!response)throw new Error('Local Worker did not become ready for document generation');
 const html=await response.text(),bytes=Buffer.byteLength(html),build=process.env.NEXT_PUBLIC_RIVEXIS_BUILD_SHA||'local';
 if(response.status!==200||response.headers.has('set-cookie')||!html.endsWith('</html>')||bytes<1000||bytes>2*1024*1024)throw new Error('Invalid or incomplete public document');
 if(!html.includes(`name="rivexis-build" content="${build}"`)||!html.includes('See beyond the position'))throw new Error('Public document does not match this build');
 for(const [name,value] of Object.entries(BASE_SECURITY_HEADERS))if(response.headers.get(name)!==value)throw new Error(`Missing public security header: ${name}`);
 // The renderer and its emitted client files must belong to the same build.
 const client=path.join(root,'dist/client');
 for(const match of html.matchAll(/(?:src|href)="(\/_next\/static\/[^"?#]+)(?:[?#][^"]*)?"/g)){
  const filename=path.resolve(client,'.'+decodeURIComponent(match[1]));
  if(!filename.startsWith(client+path.sep))throw new Error('Public asset path escaped this build');
  await fs.access(filename);
 }
 await fs.mkdir(path.dirname(asset),{recursive:true});await fs.writeFile(asset,html);
 // Direct requests to the public artifact must retain the same framing/CSP
 // protections as the canonical document, including extensionless asset URLs.
 const headerFile=path.join(client,'_headers');
 const rule='\n/_rivexis-public/*\n'+Object.entries({...BASE_SECURITY_HEADERS,'Cache-Control':'public, max-age=0, must-revalidate'}).map(([name,value])=>`  ${name}: ${value}`).join('\n')+'\n';
 await fs.appendFile(headerFile,rule);

 const manifest={build,bytes,sha256:crypto.createHash('sha256').update(html).digest('hex'),source:'Existing compiled Worker, local anonymous GET /',headersVerified:true,anonymous:true};
 await fs.writeFile(path.join(root,'dist/server/rivexis-public-document.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log('Public document build: PASS '+JSON.stringify(manifest));
}catch(error){
 console.error(diagnostics.slice(-3000));throw error;
}finally{
 if(child.pid&&child.exitCode===null){
  if(process.platform==='win32')spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});
  else{try{process.kill(-child.pid,'SIGTERM')}catch{}}
 }
}
