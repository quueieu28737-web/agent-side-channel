"""Compile the current sources and preserve R35 diagnostics."""
from pathlib import Path
import shutil
import subprocess
import sys

O = Path(__file__).resolve().parent
P = O.parents[1]
M = P / 'manuscript'
R = P.parents[1]

for script in ('build_audit_summary.py', 'review_closure.py',
               'build_source_metadata.py', 'reporting_patterns.py',
               'audit_check.py', 'r35_privacy_census.py'):
    run = subprocess.run([sys.executable, str(M/'tools'/script)], cwd=M, capture_output=True)
    (O/(script+'.txt')).write_text((run.stdout+run.stderr).decode('utf8',errors='replace').replace('\r\n','\n'),encoding='utf8',newline='\n')
    if run.returncode: raise RuntimeError('Generator failed: '+script)

for name in ('main','supplement'):
    for i,cmd in enumerate((['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],
                            ['bibtex',name],
                            ['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],
                            ['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'])):
        run = subprocess.run(cmd,cwd=M,capture_output=True)
        log = (run.stdout+run.stderr).decode('utf8',errors='replace')
        (O/(name+'-'+str(i)+'.txt')).write_text('\n'.join(s.rstrip() for s in log.splitlines())+'\n',encoding='utf8',newline='\n')
        if run.returncode: raise RuntimeError(f'{name}: {cmd[0]} failed; inspect {name}-{i}.txt')
        if cmd[0]=='bibtex':
            b=M/(name+'.bbl')
            b.write_text('\n'.join(s.rstrip() for s in b.read_text(encoding='utf8').splitlines())+'\n',encoding='utf8',newline='\n')
    print(name+' COMPILED',flush=True)

if '--publish-copies' in sys.argv:
    for name in ('main','supplement'):
        for dest in (R/(name+'.pdf'),P/'pdf'/(name+'.pdf')): shutil.copyfile(M/(name+'.pdf'),dest)
        log=(M/(name+'.log')).read_text(errors='replace')
        (P/'pdf/build-logs'/(name+'.log')).write_text('\n'.join(s.rstrip() for s in log.splitlines())+'\n',encoding='utf8',newline='\n')
        for ext in ('aux','blg','log','out','toc','lof','lot'):
            file=(M/(name+'.'+ext)).resolve()
            assert file.parent==M.resolve()
            if file.exists(): file.unlink()
    print('PDF copies published',flush=True)
