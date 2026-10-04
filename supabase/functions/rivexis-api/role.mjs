export const RIVEXIS_ROLES=Object.freeze(["Individual","Fund","Treasury","Analyst"]);
const ROLE_SET=new Set(RIVEXIS_ROLES);

export function parseRole(value){
  return typeof value==="string"&&ROLE_SET.has(value)?value:null;
}

export function roleOrDefault(value,fallback="Individual"){
  return parseRole(value)??fallback;
}
