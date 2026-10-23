"""Regenerate upstream R5 tables into a temporary directory and compare text.

The upstream table generator uses only r5lib.HERE/read; a minimal data reader
avoids loading scientific/model libraries for this presentation-only check.
"""
from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,sys,tempfile
P=Path(__file__).resolve().parents[2]
D=P/'experiments/sp2027-r5-crossfit'
sys.modules['r5lib']=SimpleNamespace(HERE=D,PROMPTS=['baseline','rules'],read=lambda p:json.loads(p.read_text(encoding='utf-8-sig')))
spec=importlib.util.spec_from_file_location('upstream_tables',D/'make_tables_r5.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as tmp:
    module.MS=Path(tmp);module.main()
    for name in ('r5-main.tex','r5-supp.tex'):
        assert (module.MS/name).read_text()==(P/'manuscript/tables'/name).read_text(),name
print('UPSTREAM_R5_TABLES_REGENERATE_FROM_SAVED_RESULTS')
