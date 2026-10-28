// Shared by framework responses and the build-generated public document.
export const BASE_SECURITY_HEADERS=Object.freeze({
 'X-Content-Type-Options':'nosniff',
 'X-Frame-Options':'DENY',
 'Referrer-Policy':'strict-origin-when-cross-origin',
 'Permissions-Policy':'camera=(), microphone=(), geolocation=()',
 'Cross-Origin-Opener-Policy':'same-origin',
 'Strict-Transport-Security':'max-age=31536000; includeSubDomains',
 'Content-Security-Policy':"object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
});
