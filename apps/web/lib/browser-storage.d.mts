type StorageArea='local'|'session';
export function readDeviceHint(area:StorageArea,key:string):string|null;
export function writeDeviceHint(area:StorageArea,key:string,value:string):void;
export function removeDeviceHint(area:StorageArea,key:string):void;
