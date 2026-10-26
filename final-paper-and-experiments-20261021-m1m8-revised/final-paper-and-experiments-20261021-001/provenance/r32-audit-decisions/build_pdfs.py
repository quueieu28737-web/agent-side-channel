"""Build current PDFs with the standard IEEE class; preserve compiler diagnostics."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,sys,shutil
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';R=P.parents[1]

def build(name):
 commands=[['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],['bibtex',name],
           ['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],
           ['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex']]
 logs=O/'compiler-output';logs.mkdir(exist_ok=True)
 for i,cmd in enumerate(commands):
  p=subprocess.run(cmd,cwd=M,capture_output=True)
  # Compiler text only: normalize CRLF and line-end whitespace for repository diffs.
  text=(p.stdout+p.stderr).decode('utf-8',errors='replace')
  (logs/f'{name}-{i}.txt').write_text('\n'.join(s.rstrip() for s in text.splitlines()).rstrip()+'\n',encoding='utf-8',newline='\n')
  if p.returncode:raise RuntimeError(f'{name}: {cmd[0]} failed; inspect compiler-output')
  if cmd[0]=='bibtex':
   b=M/(name+'.bbl');b.write_text('\n'.join(s.rstrip() for s in b.read_text().splitlines())+'\n',newline='\n')
 print(name,'COMPILED',flush=True)

if '--publish-only' not in sys.argv:
 for script in ['build_audit_summary.py','audit_check.py']:
  p=subprocess.run([sys.executable,str(M/'tools'/script)],cwd=M,capture_output=True)
  (O/(script+'.txt')).write_text((p.stdout+p.stderr).decode('utf8',errors='replace').replace('\r\n','\n'),encoding='utf8',newline='\n')
  if p.returncode:raise RuntimeError(f'Pre-build audit failed: {script}')
 with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(build,['main','supplement']))
if '--publish-copies' in sys.argv or '--publish-only' in sys.argv:
 for name in ('main','supplement'):
  for dest in (R/(name+'.pdf'),P/'pdf'/(name+'.pdf')):shutil.copyfile(M/(name+'.pdf'),dest)
  text='\n'.join(s.rstrip() for s in (M/(name+'.log')).read_text(errors='replace').splitlines()).rstrip()+'\n'
  for folder in ('provenance/r32-audit-decisions/published-build-logs','pdf/build-logs'):(P/folder).mkdir(parents=True,exist_ok=True);(P/folder/(name+'.log')).write_text(text,encoding='utf8',newline='\n')
  for ext in ('aux','blg','log','out','toc','lof','lot'):
   path=(M/(name+'.'+ext)).resolve();assert path.parent==M.resolve()
   if path.exists():path.unlink()
 print('PDF_COPIES_AND_DIAGNOSTICS_PUBLISHED',flush=True)
