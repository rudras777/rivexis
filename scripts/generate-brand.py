"""Compose the existing type outlines with the owner's ORIGINAL metallic X.
Authoring dependency: fonttools==4.66.1. Fonts are not redistributed.
Run generate-brand.py followed by export-brand.mjs to generate all consumers.
"""
import argparse,base64,json,struct
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.basePen import BasePen
from fontTools.svgLib.path import parse_path
parser=argparse.ArgumentParser();parser.add_argument('--serif',required=True);parser.add_argument('--sans',required=True)
args=parser.parse_args();root=Path(__file__).resolve().parents[1]
serif=TTFont(args.serif);sans=TTFont(args.sans)
out=root/'apps/web/public/brand';out.mkdir(parents=True,exist_ok=True)
art=(out/'rivexis-x-original.png').read_bytes()
if art[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Original logo must be PNG')
art_width,art_height=struct.unpack('>II',art[16:24])
art_uri='data:image/png;base64,'+base64.b64encode(art).decode()
def outline(font,text,x,y,scale,tracking):
    paths=[];glyphs=font.getGlyphSet();cmap=font.getBestCmap()
    for char in text:
        if char!=' ':
            glyph=glyphs[cmap[ord(char)]];pen=SVGPathPen(glyphs)
            glyph.draw(TransformPen(pen,(scale,0,0,-scale,x,y)))
            paths.append(pen.getCommands());x+=glyph.width*scale+tracking
        else:x+=font['hmtx'].metrics[cmap[ord(' ')]][0]*scale+tracking
    return ''.join(paths),x
left,x=outline(serif,'RIVE',18,129,.08,14);markX=x+2
right,end=outline(serif,'IS',markX+132+16,129,.08,14)
width=round(end+4);word=left+right
_,tagwidth=outline(sans,'RISK. VALUE. EXECUTION. ANALYSIS.',0,0,.016,2.0)
tag,_=outline(sans,'RISK. VALUE. EXECUTION. ANALYSIS.',(width-tagwidth)/2,181,.016,2.0)
def image(x,y,w,h):
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="{art_uri}"/>'
def content(ink,lockup=False):
    return f'<path fill="{ink}" d="{word}"/>'+image(markX-8,-9,148,148)+(f'<path fill="{ink}" opacity=".82" d="{tag}"/>' if lockup else '')
def svg(body,w=width,h=146):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="RIVEXIS">{body}</svg>'
for variant,ink in [('dark','#E9EBE7'),('light','#202B2D'),('ivory','#E9EBE7'),('graphite','#202B2D')]:
    for lockup in [False,True]:
        name='lockup' if lockup else 'wordmark'
        (out/f'rivexis-{name}-{variant}.svg').write_text(svg(content(ink,lockup),h=203 if lockup else 146),encoding='utf-8')
icon=image(0,0,160,160)
(out/'rivexis-symbol.svg').write_text(svg('<rect width="160" height="160" rx="28" fill="#141B1D"/>'+icon,160,160),encoding='utf-8')
(out/'rivexis-symbol-transparent.svg').write_text(svg(icon,160,160),encoding='utf-8')
(out/'rivexis-compact.svg').write_text(svg(icon,160,160),encoding='utf-8')
report=svg(content('#202B2D',True),h=203)
(out/'rivexis-report-header.svg').write_text(report,encoding='utf-8')
geometry={'width':width,'wordmark':word,'tagline':tag,'markX':markX,'artwork':'/brand/rivexis-x-original.png','artworkWidth':art_width,'artworkHeight':art_height}
(root/'apps/web/components/brand-geometry.ts').write_text('// Generated: outlined type plus the original supplied metallic artwork, never a traced substitute.\nexport const brandGeometry='+json.dumps(geometry,separators=(',',':'))+' as const;\n',encoding='utf-8')
class PdfPen(BasePen):
    def __init__(self):super().__init__(None);self.commands=[]
    def point(self,p):return ' '.join(f'{n:.5f}'.rstrip('0').rstrip('.') for n in p)
    def _moveTo(self,p):self.commands.append(self.point(p)+' m')
    def _lineTo(self,p):self.commands.append(self.point(p)+' l')
    def _curveToOne(self,a,b,c):self.commands.append(' '.join(self.point(p) for p in [a,b,c])+' c')
    def _closePath(self):self.commands.append('h')
    def _endPath(self):pass
def pdf_path(path):
    pen=PdfPen();parse_path(path,pen);return '\n'.join(pen.commands)+'\nf'
# Preserve the existing PDF coordinate system and outlined type. The original X
# is embedded separately by the PDF renderer; no network/font fetch is needed.
pdf='q\n0.21 0 0 -0.21 72 768 cm\n0.12549 0.16863 0.17647 rg\n'+pdf_path(word)+'\n'+pdf_path(tag)+'\nQ\nq\n31.08 0 0 31.08 '+str(round(72+(markX-8)*.21,5))+' 738.81 cm\n/RvxX Do\nQ'
(root/'supabase/functions/rivexis-api/brand.mjs').write_text('// Generated from the original supplied artwork. No remote assets or fonts.\nexport const BRAND_REPORT_SVG='+json.dumps(report)+';\nexport const BRAND_PDF_HEADER='+json.dumps(pdf)+';\n',encoding='utf-8')
print(f'Composed original {art_width}x{art_height} artwork; outlined lockup {width}x203. Run export-brand.mjs next.')
