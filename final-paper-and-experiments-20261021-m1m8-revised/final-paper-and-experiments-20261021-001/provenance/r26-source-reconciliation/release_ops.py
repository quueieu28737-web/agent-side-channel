"""Assemble the R26 literature-SoK and appendix-case release."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,sys,zipfile
from pypdf import PdfReader
O=Path(__file__).resolve().parent;P=O.parents[1];R=P.parents[1];M=P/'manuscript'
sys.path.insert(0,str(P))
from verify_package import closure
def read(f): return json.loads(f.read_text(encoding='utf-8-sig'))
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(f,v):f.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def anonymous():
 members={}
 for name in ['main','supplement']:
  for rel in closure(M,name+'.tex'):members['manuscript/'+rel]=(M/rel).read_bytes()
  members[name+'.pdf']=(P/'pdf'/(name+'.pdf')).read_bytes()
 for extra in ['IEEEtran.cls','IEEEtran.bst']:
  loc=subprocess.run(['kpsewhich',extra],capture_output=True,text=True,check=True).stdout.strip()
  assert loc,extra
  members['manuscript/'+extra]=Path(loc).read_bytes()
 members['manuscript/placeins.sty']=(M/'placeins.sty').read_bytes()
 members['README.txt']=b'Anonymous paper and LaTeX sources. Build each entry using pdfLaTeX, BibTeX, pdfLaTeX twice with IEEEtran. This archive contains the paper and supplement, not the full experimental artifact. The experimental artifact requires a separately hosted anonymous immutable snapshot. Source author names in third-party citations are retained. No development history or machine-specific compiler logs are included.\n'
 patterns=[b'quueieu28737',b'c:/users/',b'c:\\users\\',b'github.com/quueieu']
 for name,data in members.items():
  if name.endswith(('.tex','.bib','.txt')):
   assert not any(x in data.lower() for x in patterns),name
 for name in ['main','supplement']:
  d=PdfReader(P/'pdf'/(name+'.pdf'))
  txt=(str(d.metadata)+'\n'+'\n'.join(x.extract_text() for x in d.pages)).lower()
  assert not any(x.decode() in txt for x in patterns),name
 z=O/'anonymous-paper-source.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as f:
  for name,data in sorted(members.items()):
   info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   f.writestr(info,data)
 with zipfile.ZipFile(z) as f:
  assert f.testzip() is None
  assert {n:hashlib.sha256(f.read(n)).hexdigest() for n in f.namelist()}=={n:hashlib.sha256(b).hexdigest() for n,b in members.items()}
 save(O/'anonymous-paper-check.json',{'status':'PAPER_SOURCE_BUNDLE_SCAN_PASS','archive_sha256':sha(z),'members':{n:hashlib.sha256(b).hexdigest() for n,b in members.items()},'scope':'Paper PDFs and source closure only; not anonymous hosting or the full experimental artifact','checked_patterns':[x.decode() for x in patterns]})
 print('ANONYMOUS_PAPER_BUNDLE_PASS',len(members))
def manifest():
 paths=[]
 def walk(folder):
  for f in folder.iterdir():
   rel=f.relative_to(P).as_posix()
   if rel=='experiments/sp2027-r4' or f.name=='__pycache__':continue
   assert not f.is_symlink(),f
   if f.is_dir():walk(f)
   elif rel!='SHA256SUMS.json':
    assert f.stat().st_size<100*1024**2,rel
    paths.append(f)
 walk(P);paths.sort()
 for raw in ['connectivity','pilot','formal']:assert not (P/'experiments/sp2027-r7-agent-extension'/raw).exists()
 with ThreadPoolExecutor(max_workers=10) as pool:files={f.relative_to(P).as_posix():h for f,h in zip(paths,pool.map(sha,paths))}
 save(P/'SHA256SUMS.json',{'algorithm':'SHA-256','local_only_directories':['experiments/sp2027-r4'],'files':files})
 print('R26_MANIFEST',len(files))
if __name__=='__main__':{'anonymous':anonymous,'manifest':manifest}[sys.argv[1]]()
