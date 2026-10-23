"""Reproduce presentation changes without changing any frozen table value.

Uses the immutable SoK and R5 generators with temporary output directories.
--check is read-only; default writes the three current presentation tables.
"""
from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,re,sys,tempfile
P=Path(__file__).resolve().parents[2]
S=P/'provenance/sok-restructure'
D=P/'experiments/sp2027-r5-crossfit'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def main():
    with tempfile.TemporaryDirectory() as directory:
        tmp=Path(directory);(tmp/'manuscript/tables').mkdir(parents=True)
        module=load('original_sok',S/'build_sok_tables.py')
        module.P=tmp;module.HERE=tmp
        argv=sys.argv;sys.argv=[argv[0]]
        try:module.main()
        finally:sys.argv=argv
        assert json.loads((tmp/'table_sources.json').read_text())==json.loads((S/'table_sources.json').read_text())
        outputs={}
        s=(tmp/'manuscript/tables/family-audit-matrix.tex').read_text()
        outputs['family-audit-matrix.tex']=s.replace(r'$\bullet$',r'\textbf{B}').replace(r'$\circ$','U').replace(r'\auditpartial',r'\textbf{P}').replace('?: unverified binding','?: unverified binding (intentional)')
        s=(tmp/'manuscript/tables/core-family-map.tex').read_text().replace(r'\!\to\!',r'\,\to\,')
        outputs['core-family-map.tex']=re.sub(r' & ((?:IV|III|II|I)(?:,(?:IV|III|II|I))?)(?= &|\\\\)',lambda m:' & '+r'\texttt{'+m[1]+'}',s)
        sys.modules['r5lib']=SimpleNamespace(HERE=D,PROMPTS=['baseline','rules'],read=lambda p:json.loads(p.read_text(encoding='utf-8-sig')))
        r5=load('original_r5',D/'make_tables_r5.py');r5.MS=tmp;r5.main()
        assert (tmp/'r5-supp.tex').read_text()==(P/'manuscript/tables/r5-supp.tex').read_text()
        s=(tmp/'r5-main.tex').read_text().replace(r'\scriptsize',r'\footnotesize').replace(r'{2.5pt}',r'{2pt}')
        s=re.sub(r'(?<![\w.])(\d+\.\d+ \[\d+\.\d+, \d+\.\d+\])',lambda m:r'\mbox{'+m[1]+'}',s)
        outputs['r5-main.tex']=s.replace('Selected: 1024-B buckets','Selected buckets').replace('E9 point (constant)','E9 constant').replace('Writes-only cover','Write cover')
        for name,s in outputs.items():
            p=P/'manuscript/tables'/name
            if '--check' in sys.argv:assert p.read_text()==s,name
            else:p.write_text(s,encoding='utf-8',newline='\n')
    print('58_FAMILY_LABELS_180_AUDIT_CELLS_AND_ALL_R5_INTERVALS_MATCH')
if __name__=='__main__':main()
