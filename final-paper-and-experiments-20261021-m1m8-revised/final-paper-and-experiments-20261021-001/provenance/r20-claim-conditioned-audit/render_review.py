"""Render every delivered page and overview sheets using Poppler/Pillow."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
from pypdf import PdfReader
import subprocess,json
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1];V=R/'revision-preview/r20-delivery';V.mkdir(parents=True,exist_ok=True)
def render(name):
 folder=V/name;folder.mkdir(exist_ok=True)
 subprocess.run(['pdftoppm','-scale-to','900','-png',str(M/(name+'.pdf')),str(folder/'page')],check=True,capture_output=True)
 pages=sorted(folder.glob('page-*.png'))
 for start in range(0,len(pages),12):
  sheet=Image.new('RGB',(1800,1800),'#c8c8c8');draw=ImageDraw.Draw(sheet)
  for j,f in enumerate(pages[start:start+12]):
   im=Image.open(f).convert('RGB');im.thumbnail((440,565));x=(j%4)*450+(450-im.width)//2;y=(j//4)*600+24
   sheet.paste(im,(x,y));draw.text(((j%4)*450+8,(j//4)*600+5),f'{name} page {start+j+1}',fill='black')
  sheet.save(V/f'{name}-overview-{start+1:02d}.png')
 d=PdfReader(M/(name+'.pdf'))
 (V/(name+'.txt')).write_text('\n'.join(f'\nPAGE {i+1}\n'+p.extract_text() for i,p in enumerate(d.pages)),encoding='utf8')
 print(name,len(pages),'rendered',flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(render,['main','supplement']))

for name,indices in [('main',[1,2,7,13]),('supplement',[58,59,60])]:
 for n in indices:
  subprocess.run(['pdftoppm','-f',str(n),'-l',str(n),'-scale-to','1700','-singlefile','-png',str(M/(name+'.pdf')),str(V/f'{name}-zoom-{n}')],check=True,capture_output=True)
print('ZOOMS_RENDERED',flush=True)
