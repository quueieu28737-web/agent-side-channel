"""Render all current PDF pages for human/visual inspection; never auto-approve QA."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
import hashlib, json, subprocess, sys

O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1]
target=(R/'revision-preview'/('r7-final-render' if '--final' in sys.argv else 'r7-draft-render')).resolve()
target.mkdir(parents=True,exist_ok=True)

def one(name):
 source=P/('pdf' if '--final' in sys.argv else 'manuscript')/(name+'.pdf')
 folder=target/name;folder.mkdir(exist_ok=True)
 subprocess.run(['pdftoppm','-r','110','-png',str(source),str(folder/'page')],check=True,capture_output=True)
 pages=sorted(folder.glob('page-*.png'))
 # Remove no files: a PDF page count check catches stale render directories.
 from pypdf import PdfReader
 assert len(pages)==len(PdfReader(source).pages),(name,len(pages))
 contacts=[]
 for start in range(0,len(pages),6):
  chunk=pages[start:start+6]
  sheet=Image.new('RGB',(900,1794),'#d9dfe5');draw=ImageDraw.Draw(sheet)
  for j,path in enumerate(chunk):
   im=Image.open(path).convert('RGB');im.thumbnail((430,556))
   x=10+(j%2)*450;y=28+(j//2)*598
   sheet.paste(im,(x,y));draw.text((x,y-19),name+' / '+str(start+j+1),fill='black')
  out=folder/f'contact-{start+1:02d}-{start+len(chunk):02d}.png';sheet.save(out);contacts.append(str(out))
 return name,{'pdf_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pages':len(pages),'page_images':[str(p) for p in pages],'contact_sheets':contacts}

with ThreadPoolExecutor(max_workers=2) as pool:result=dict(pool.map(one,['main','supplement']))
(target/'render_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:{'pages':v['pages'],'contact_sheets':v['contact_sheets']} for k,v in result.items()},indent=2))
