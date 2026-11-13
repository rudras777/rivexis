import {expect,test} from './browser-test';

const cases=[
  {name:'login',path:'/login',endpoint:'/api/v1/auth/web/login',fields:[['Email','fixture@example.invalid'],['Password','synthetic-password-123']],button:'Log in',status:401,body:{detail:'Invalid credentials'},feedback:'Invalid email or password.'},
  {name:'signup',path:'/signup',endpoint:'/api/v1/auth/web/signup',fields:[['Email','fixture@example.invalid'],['Password','synthetic-password-123']],button:'Continue',status:200,body:{verification_required:true,email_status:'accepted'},feedback:'Follow the instructions in the email to confirm your address.'},
  {name:'recovery request',path:'/forgot-password',endpoint:'/api/v1/auth/password-reset/request',fields:[['Email','fixture@example.invalid']],button:'Send reset link',status:202,body:{status:'accepted'},feedback:'Recovery request received.'},
  {name:'verification resend',path:'/verify-email',endpoint:'/api/v1/auth/email-verification/request',fields:[['Email','fixture@example.invalid']],button:'Send verification email',status:202,body:{status:'accepted'},feedback:'Verification request received.'},
  {name:'verification code',path:'/verify-email',endpoint:'/api/v1/auth/email-verification/confirm',fields:[['Email','fixture@example.invalid'],['Verification code','synthetic-code']],button:'Verify account',status:400,body:{detail:'Invalid code'},feedback:'This verification code is invalid or expired.'},
  {name:'password update',path:'/reset-password',endpoint:'/api/v1/auth/password-reset/confirm',fields:[['Recovery token','synthetic-code'],['Email','fixture@example.invalid'],['New password','synthetic-password-123'],['Confirm new password','synthetic-password-123']],button:'Update password',status:400,body:{detail:'Invalid recovery'},feedback:'This recovery link is invalid or expired.'},
] as const;

for(const scenario of cases)test(`delayed JavaScript never loses a ${scenario.name} submission to native navigation`,async({page})=>{
  let releaseScripts!:()=>void;
  const scriptsReady=new Promise<void>(resolve=>{releaseScripts=resolve});
  await page.route('**/*',async route=>{
    if(route.request().resourceType()==='script'||new URL(route.request().url()).pathname.endsWith('.js'))await scriptsReady;
    await route.continue();
  });
  await page.route('**/health',route=>route.fulfill({status:200,json:{status:'ready'}}));
  await page.route('**/api/v1/auth/session-status',route=>route.fulfill({status:200,json:{authenticated:false,email_verified:false}}));
  let apiPosts=0,nativePosts=0;
  page.on('request',request=>{if(request.method()==='POST'&&new URL(request.url()).pathname===scenario.path)nativePosts++});
  await page.route(`**${scenario.endpoint}`,route=>{apiPosts++;return route.fulfill({status:scenario.status,json:scenario.body})});
  try{
    await page.goto(scenario.path,{waitUntil:'commit'});
    const fields=page.locator('.formCard input:not([type="hidden"])');
    await expect(fields.first()).toBeVisible();
    for(const field of await fields.all())await expect(field).toBeDisabled();
    for(const button of await page.locator('.formCard button[type="submit"]').all())await expect(button).toBeDisabled();
  }finally{releaseScripts()}
  for(const [label,value] of scenario.fields)await page.getByRole('textbox',{name:label,exact:true}).or(page.getByLabel(label,{exact:true})).fill(value);
  await page.getByRole('button',{name:scenario.button,exact:true}).click();
  await expect(page.locator('.formCard [role="alert"], .formCard [role="status"]')).toContainText(scenario.feedback);
  expect(apiPosts).toBe(1);expect(nativePosts).toBe(0);
  if(scenario.name==='signup')await expect(page.getByLabel('Email',{exact:true})).toHaveValue('fixture@example.invalid');
});
