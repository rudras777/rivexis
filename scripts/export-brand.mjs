// Preserve the supplied PNG and its geometry; apply the approved website tones.
import sharp from 'sharp';
import {fileURLToPath} from 'node:url';
import {readFile,writeFile,readdir} from 'node:fs/promises';
const root=new URL('../apps/web/public/brand/',import.meta.url);
const read=name=>readFile(new URL(name,root));
const original=await read('rivexis-x-original.png');
const {width:artWidth,height:artHeight}=await sharp(original).metadata();
// Map navy/blue into graphite/teal and silver highlights into ivory in sRGB.
// The alpha row is identity: no tracing, blur, reshaping or new highlights.
const matrix='0.3588235294 0.3588235294 0.1176470588 0 0.0784313725 0.2490196078 0.2490196078 0.3176470588 0 0.1058823529 0.2450980392 0.2450980392 0.3019607843 0 0.1137254902 0 0 0 1 0';
const treatment=`<svg xmlns="http://www.w3.org/2000/svg" width="${artWidth}" height="${artHeight}"><defs><filter id="tone" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="${matrix}"/></filter></defs><image width="${artWidth}" height="${artHeight}" filter="url(#tone)" href="data:image/png;base64,${original.toString('base64')}"/></svg>`;
const toned=await sharp(Buffer.from(treatment)).png().toBuffer();
const inputPixels=await sharp(original).ensureAlpha().raw().toBuffer();
const outputPixels=await sharp(toned).ensureAlpha().raw().toBuffer();
if(inputPixels.length!==outputPixels.length)throw new Error('Logo dimensions changed');
for(let i=3;i<inputPixels.length;i+=4)if(inputPixels[i]!==outputPixels[i])throw new Error('Logo alpha/outline changed');
await writeFile(new URL('rivexis-x-teal.png',root),toned);
for(const name of (await readdir(root)).filter(name=>name.endsWith('.svg'))){
 const svg=(await read(name)).toString();
 if(!svg.includes('href="data:image/png;base64,'))throw new Error('Missing original image in '+name);
 await writeFile(new URL(name,root),svg.replace(/href="data:image\/png;base64,[^"]+"/g,'href="data:image/png;base64,'+toned.toString('base64')+'"'));
}
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
const reportArt=await sharp(toned).resize(320,320).png().toBuffer();
const printArt=await sharp(toned).resize(512,512).flatten({background:'#ffffff'}).jpeg({quality:100,chromaSubsampling:'4:4:4'}).toBuffer();
const brandFile=new URL('../supabase/functions/rivexis-api/brand.mjs',import.meta.url);
let brand=await readFile(brandFile,'utf8');
const reportLine=brand.match(/^export const BRAND_REPORT_SVG=(.*);$/m);
if(!reportLine)throw new Error('Generated report identity missing');
const reportSvg=JSON.parse(reportLine[1]).replace(/href="data:image\/png;base64,[^"]+"/g,'href="data:image/png;base64,'+reportArt.toString('base64')+'"');
brand=brand.replace(reportLine[0],'export const BRAND_REPORT_SVG='+JSON.stringify(reportSvg)+';').replace(/^export const BRAND_PDF_X_HEX=.*;\r?\n?/m,'');
brand+='export const BRAND_PDF_X_HEX='+JSON.stringify(printArt.toString('hex'))+';\n';
await writeFile(brandFile,brand);
console.log('Website tones exported with identical source alpha/outline; original PNG preserved.');
