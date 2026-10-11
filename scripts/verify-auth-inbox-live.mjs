// Explicitly opt-in, isolated production QA. No credentials, cookies, or mail bodies are recorded.
import {randomBytes,createHash} from 'node:crypto';
import {createInterface} from 'node:readline';
import {writeFile} from 'node:fs/promises';
import {chromium} from '@playwright/test';
const base='https://rivexis-web.rudrasingh0718.workers.dev';
const email=process.env.RIVEXIS_AUTH_QA_EMAIL;
if(process.env.RIVEXIS_AUTH_QA_MUTATIONS!=='isolated-test-account-only'||!email?.match(/\+rivexisrelease\d+@gmail\.com$/))throw new Error('Explicit isolated QA account opt-in required');
const checks=[];
const record=(name,pass,details={})=>{checks.push({name,pass,...details});console.log(JSON.stringify({name,pass,...details}));if(!pass)throw new Error(`Verification failed: ${name}`)};
let password=randomBytes(24).toString('base64url')+'!aA7';
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({baseURL:base});
const page=await context.newPage();
const post=(route,data)=>context.request.post(route,{data,headers:{Origin:base}});
const recoveryOnly=process.env.RIVEXIS_AUTH_QA_RECOVERY_ONLY==='1';
if(!recoveryOnly){
await page.goto('/signup?next=%2Fworkspace%2Fsettings');
await page.getByLabel('Email',{exact:true}).fill(email);
await page.getByLabel('Password',{exact:true}).fill(password);
const signup=page.waitForResponse(r=>r.url().endsWith('/api/v1/auth/web/signup')&&r.request().method()==='POST');
await page.getByRole('button',{name:'Continue',exact:true}).click();
const response=await signup;const result=await response.json();
record('real_signup_requests_verification',response.status()===200&&result.verification_required===true,{http:response.status()});
await page.waitForURL(/\/verify-email/);
record('unverified_workspace_denied',(await context.request.get('/api/v1/account/settings')).status()===401);
const premature=await post('/api/v1/auth/web/login',{email,password});
record('unverified_password_login_denied',premature.status()===403,{http:premature.status()});
console.log(JSON.stringify({awaiting:'confirmation_email',recipientFingerprint:createHash('sha256').update(email).digest('hex').slice(0,12)}));
}else{
 record('fresh_recovery_requested',(await post('/api/v1/auth/password-reset/request',{email})).status()===202);
 console.log(JSON.stringify({awaiting:'recovery_email'}));
}
if(process.stdin.isTTY)process.stdin.setRawMode(true); // Keep mail credentials out of PTY echo.
const commands=createInterface({input:process.stdin,terminal:false,crlfDelay:Infinity});
async function providerLink(url){
 const parsed=new URL(url);if(parsed.protocol!=='https:')throw new Error('HTTPS mail link required');
 if(/(^|\.)sendibt\d+\.com$/.test(parsed.hostname)){
  const tracking=await context.request.get(url,{maxRedirects:0});
  url=tracking.headers().location;
 }
 const target=new URL(url);
 if(target.origin!=='https://ivszvufdonfgwjpfgwii.supabase.co'||target.pathname!=='/auth/v1/verify')throw new Error('Unexpected confirmation destination');
 return target;
}
try{for await(const line of commands){const command=JSON.parse(line);
 if(command.op==='confirm'){
  const link=await providerLink(command.url);
  const reply=await context.request.get(link.href,{maxRedirects:0});
  const destination=new URL(reply.headers().location);
  record('inbox_confirmation_link_verified',reply.status()===303&&destination.origin===base&&!destination.hash.includes('error='),{http:reply.status()});
  await page.goto(destination.href);
  await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);
  const firstLogin=page.waitForResponse(r=>r.url().endsWith('/api/v1/auth/web/login')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Log in',exact:true}).click();
  record('confirmed_qa_real_form_login',(await firstLogin).status()===200);
  await page.waitForURL(/\/workspace/);
  const profile=await context.request.get('/api/v1/account/settings');
  record('verified_owner_settings_available',profile.status()===200,{http:profile.status()});
  record('fresh_recovery_requested',(await post('/api/v1/auth/password-reset/request',{email})).status()===202);
  console.log(JSON.stringify({awaiting:'recovery_email'}));
 }else if(command.op==='recover'){
  const recoveryLink=await providerLink(command.url);
  const tokenHash=recoveryLink.searchParams.get('token');
  if(recoveryLink.searchParams.get('type')!=='recovery'||!tokenHash)throw new Error('Invalid recovery mail link');
  const newPassword=randomBytes(24).toString('base64url')+'!aA8';
  // This changes only the newly-created disposable QA identity, never an existing user.
  const recovered=await post('/api/v1/auth/password-reset/confirm',{token_hash:tokenHash,password:newPassword});
  record('fresh_inbox_recovery_completed',recovered.status()===200,{http:recovered.status()});
  const oldLogin=await post('/api/v1/auth/web/login',{email,password});
  record(recoveryOnly?'unrelated_password_rejected':'old_qa_password_rejected',oldLogin.status()===401,{http:oldLogin.status()});
  password=newPassword;
  await context.clearCookies();await page.goto('/login?next=%2Fworkspace%2Fsettings');
  await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);
  const login=page.waitForResponse(r=>r.url().endsWith('/api/v1/auth/web/login')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Log in',exact:true}).click();
  record('new_qa_password_real_login',(await login).status()===200);
  await page.waitForURL(/\/workspace/);
  const workspaces=await (await context.request.get('/api/v1/workspaces')).json();
  if(!workspaces.items?.length){
   await page.goto('/onboarding?next=%2Fworkspace%2Fsettings');
   await page.getByLabel('Workspace name').fill('Release QA Workspace');
   const created=page.waitForResponse(r=>r.url().endsWith('/api/v1/workspaces')&&r.request().method()==='POST');
   await page.getByRole('button',{name:'Open workspace',exact:true}).click();
   record('new_qa_workspace_onboarding',(await created).ok());
  }else await page.goto('/workspace/settings');
  await page.waitForURL(/\/workspace\/settings/);await page.getByRole('heading',{name:'Settings',exact:true}).waitFor();
  record('real_settings_ui_after_onboarding',true);
  const status=await (await context.request.get('/api/v1/auth/session-status')).json();
  record('recovered_login_is_verified',status.authenticated===true&&status.email_verified===true);
  const replay=await post('/api/v1/auth/password-reset/confirm',{token_hash:tokenHash,password:randomBytes(24).toString('base64url')+'!aA9'});
  record('recovery_link_replay_denied',replay.status()===400,{http:replay.status()});
  const csrf=await (await context.request.get('/api/v1/auth/web/csrf')).json();
  const logout=await context.request.post('/api/v1/auth/logout',{headers:{Origin:base,'X-Rivexis-CSRF':csrf.csrf_token},data:{}});
  record('qa_logout_succeeds',logout.ok(),{http:logout.status()});
  record('logged_out_settings_denied',(await context.request.get('/api/v1/account/settings')).status()===401);
  const html=await (await context.request.get('/')).text();const sha=html.match(/name="rivexis-build" content="([a-f0-9]{40})"/)?.[1]??null;
  const audit={testedAt:new Date().toISOString(),base,buildSha:sha,checks,credentialsRecorded:false,existingAccountChanged:false,qaAccountRetained:true,providerMailEvidence:command.mailEvidence??null};
  if(process.env.RIVEXIS_AUTH_QA_OUTPUT)await writeFile(process.env.RIVEXIS_AUTH_QA_OUTPUT,JSON.stringify(audit,null,2));
  console.log(JSON.stringify({complete:true,passed:checks.length,buildSha:sha}));break;
 }else if(command.op==='stop'){break}else throw new Error('Unknown QA command');
}}catch{process.exitCode=1;console.error('QA verification stopped. Review the sanitized check results; credentials are not emitted.')}finally{password='';await browser.close();commands.close()}
