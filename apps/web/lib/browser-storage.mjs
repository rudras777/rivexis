// Optional device hints only. Server cookies and authorization remain authoritative.
// A browser can deny access to the storage object itself, or any of its methods.
function deviceStorage(area){
  return typeof window==='undefined'?null:area==='local'?window.localStorage:window.sessionStorage;
}
export function readDeviceHint(area,key){
  try{return deviceStorage(area)?.getItem(key)??null}catch{return null}
}
export function writeDeviceHint(area,key,value){
  try{deviceStorage(area)?.setItem(key,value)}catch{}
}
export function removeDeviceHint(area,key){
  try{deviceStorage(area)?.removeItem(key)}catch{}
}
