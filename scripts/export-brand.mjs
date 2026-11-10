// Preserve the supplied PNG byte-for-byte; icons/print are sized exports.
import sharp from 'sharp';
import {fileURLToPath} from 'node:url';
import {readFile,writeFile} from 'node:fs/promises';
const root=new URL('../apps/web/public/brand/',import.meta.url);
const read=name=>readFile(new URL(name,root));
const original=await read('rivexis-x-original.png');
for(const [source,target,width] of [
 ['rivexis-wordmark-dark.svg','rivexis-wordmark.png',4096],
 ['rivexis-wordmark-light.svg','rivexis-wordmark-light.png',4096],
 ['rivexis-lockup-dark.svg','rivexis-lockup.png',4096],
 ['rivexis-lockup-light.svg','rivexis-lockup-light.png',4096],
 ['rivexis-report-header.svg','rivexis-report-header.png',4096],
 ['rivexis-symbol.svg','rivexis-mark.png',1254],
 ['rivexis-symbol.svg','rivexis-icon.png',32],
 ['rivexis-symbol.svg','apple-touch-icon.png',180],
 ['rivexis-symbol.svg','icon-192.png',192],
 ['rivexis-symbol.svg','icon-512.png',512],
])await sharp(await read(source)).resize({width}).png().toFile(fileURLToPath(new URL(target,root)));
const sizes=[16,32,48,64,128,256];
const iconImages=await Promise.all(sizes.map(async size=>sharp(await read('rivexis-symbol.svg')).resize(size,size).png().toBuffer()));
const header=Buffer.alloc(6+16*iconImages.length);header.writeUInt16LE(1,2);header.writeUInt16LE(iconImages.length,4);let offset=header.length;
iconImages.forEach((buffer,i)=>{const pos=6+16*i,size=sizes[i];header[pos]=size===256?0:size;header[pos+1]=size===256?0:size;header.writeUInt16LE(1,pos+4);header.writeUInt16LE(32,pos+6);header.writeUInt32LE(buffer.length,pos+8);header.writeUInt32LE(offset,pos+12);offset+=buffer.length});
await writeFile(new URL('../apps/web/public/favicon.ico',import.meta.url),Buffer.concat([header,...iconImages]));
const logo=(await read('rivexis-lockup-dark.svg')).toString();
const share=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#141B1D"/><path d="M90 105H1110M90 525H1110" stroke="#303E40"/><svg x="145" y="205" width="910" height="229" viewBox="0 0 821 203">${logo.replace(/^.*?<svg[^>]*>/,'').replace(/<\/svg>$/,'')}</svg><text x="600" y="486" text-anchor="middle" fill="#B8C3BE" font-family="Arial,sans-serif" font-size="20" letter-spacing="1">DeFi Risk &amp; Decision Intelligence</text></svg>`;
await writeFile(new URL('rivexis-social.svg',root),share);await sharp(Buffer.from(share)).png().toFile(fileURLToPath(new URL('rivexis-social.png',root)));
// Reports use an appropriately sized embedded copy instead of carrying a
// megabyte-scale original in every HTML response. The supplied geometry stays.
const reportArt=await sharp(original).resize(320,320).png().toBuffer();
const printArt=await sharp(original).resize(512,512).flatten({background:'#ffffff'}).jpeg({quality:100,chromaSubsampling:'4:4:4'}).toBuffer();
const brandFile=new URL('../supabase/functions/rivexis-api/brand.mjs',import.meta.url);
let brand=(await readFile(brandFile,'utf8')).replace('data:image/png;base64,'+original.toString('base64'),'data:image/png;base64,'+reportArt.toString('base64')).replace(/^export const BRAND_PDF_X_HEX=.*;\r?\n?/m,'');
brand+='export const BRAND_PDF_X_HEX='+JSON.stringify(printArt.toString('hex'))+';\n';
await writeFile(brandFile,brand);
console.log('Original PNG preserved; high-resolution wordmarks, icons and embedded print artwork exported.');
