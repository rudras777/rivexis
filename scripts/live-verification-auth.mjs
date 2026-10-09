// Optional command-line verification uses an operator's explicit environment.
// Never discover/import browser cookies or print these headers.
export function liveVerificationHeaders(){
  const cookie=process.env.RIVEXIS_LIVE_SESSION_COOKIE,csrf=process.env.RIVEXIS_LIVE_CSRF;
  if(!cookie||!csrf)throw new Error('Live financial verification requires an explicitly supplied verified session and CSRF in RIVEXIS_LIVE_SESSION_COOKIE / RIVEXIS_LIVE_CSRF. Alternatively verify through the authenticated product UI. Public access must remain denied.');
  if(/[\r\n]/.test(cookie+csrf))throw new Error('Invalid verification header format');
  return {'content-type':'application/json',cookie,'x-rivexis-csrf':csrf};
}
