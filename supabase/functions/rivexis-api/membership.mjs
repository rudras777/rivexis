export function createMembershipClaimToken(){
  const bytes=new Uint8Array(32);
  crypto.getRandomValues(bytes);
  let binary="";
  for(const byte of bytes)binary+=String.fromCharCode(byte);
  return btoa(binary).replaceAll("+","-").replaceAll("/","_").replaceAll("=","");
}

export async function hashMembershipClaimToken(token){
  if(typeof token!=="string"||token.length<32||token.length>256)throw new Error("Invalid membership claim token");
  const digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(token));
  return Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,"0")).join("");
}
