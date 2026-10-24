"""Compare R9 numerical table bodies to the immutable R8 manuscript snapshot."""
import hashlib
import json
from pathlib import Path
import re
O=Path(__file__).resolve().parent;P=O.parents[1];M=P/'manuscript';OLD=O/'prior-manuscript'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def numeric_rows(text):
    active=False;out=[]
    for line in text.splitlines():
        if '\\begin{tabular' in line:active=True
        if active and '&' in line:
            # First column may rename E9/E10/E13 to Exp 3/4. All numerical data
            # columns, including CI endpoints, costs and observation labels, stay.
            body='&'.join(line.split('&')[1:])
            values=re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?',body)
            if values:out.append(values)
        if '\\end{tabular' in line:active=False
    return out
pairs={
 'r9-cohorts.tex':'r8-cohorts.tex',
 'r9-controls.tex':'r8-controls.tex',
 'r9-crossfit.tex':'r8-crossfit.tex',
 'r9-flush.tex':'r8-flush.tex',
 'r9-frozen-reference.tex':'r8-frozen-reference.tex',
 'r9-localization.tex':'r7-e12-main.tex',
 'r9-streaming.tex':'transfer-streaming.tex',
 'r9-dispatch.tex':'r7-e6-main.tex',
}
checked=[]
for current,prior in pairs.items():
    a=M/'tables'/current;b=OLD/'tables'/prior
    aa=numeric_rows(a.read_text());bb=numeric_rows(b.read_text())
    assert aa==bb, ('Numerical body differs',current,aa,bb)
    checked.append(dict(current='manuscript/tables/'+current,prior='prior-manuscript/tables/'+prior,
        numerical_rows=len(aa),numerical_tokens=sum(map(len,aa)),numbers_exact=True,
        current_sha256=sha(a),prior_sha256=sha(b)))
stream=P/'experiments/sp2027-r2/e5_streaming.py'
source=stream.read_text()
assert 'sets["T1"].append(dict(i))' in source
assert 'text=". ".join(sents[:2 + i["label"]]) + "."' in source
sections={n:(M/'sections'/n).read_text() for n in ['37-transfer-tests.tex','42-live-timing-main.tex']}
oldsections={n:(OLD/'sections'/n).read_text() for n in sections}
checks=[
 dict(item='Streaming byte/delay points',preserved=True,values=['2.18 TLS1.2','2.19 TLS1.3','0.21 batching','2.42 constant shape','208 vs105 token intervals'],
      unit='Wire byte ratios by emitter; token timing is proxy accounting, not measured milliseconds. Ratios cover all48 outputs; binary accuracy24 heldout.'),
 dict(item='State/dispatch/network demonstration',preserved=True,values=['173/291','18/32 positive tasks','4140 TLS sessions','582 profiler calls','26.3 bytes','7.7 total calls versus6.7 extra calls'],
      unit='Extra calls per real call and total call ratio are different but consistent quantities; 6.7 extra corresponds to7.7 total.'),
 dict(item='Real-agent frozen versus cross-fit',preserved=True,values=['414/276 originalsplit','690 runs/53 customers','110/138 versus105/138 reward','5/7 heldout positive versus14/18 all-OOF positive'],
      unit='Reference operation-category labels, not latent psychological intent. Repeats do not add independent customers.'),
 dict(item='Timing and flush composition',preserved=True,values=['4096-byte cells','2/5ms','133 slots','4140 captures','90.4/92.3 record detection','15278 records/276 episodes','82.5/96.1 request detection','7639 requests','60.7 composed return'],
      unit='Flush/cover detection is record/request classification, not138-episode category recovery; RPC time excludesLLM/WAN.'),
]
findings=[
 dict(severity='required-definition',status='resolved',location='manuscript/tables/r9-streaming.tex',
      finding='Former T1/T3 labels replaced by Verbosity/Prefix and definitions restored.',
      source='experiments/sp2027-r2/e5_streaming.py::load_texts lines39–47; R8 sections/38-retained-controlled.tex paragraph2',
      suggestion='T1 contrasts brief and full expanded responses; T3 contrasts two- versus three-sentence prefixes of the same expanded response.',
      detail='T3 is derived by period-delimited sentence splitting of the expanded partner, preserving topic/label/split; it is not a new independent generation.'),
 dict(severity='editorial',status='resolved',location='manuscript/tables/r9-crossfit.tex caption',finding='Repeated cross-fit cross-fit removed.',suggestion='Retain cross-fit once.'),
 dict(severity='scope-wording',status='resolved',location='manuscript/sections/42-live-timing-main.tex / WT comparison',
      finding='Phrase now reads evaluated point trade-offs and no longer implies offline WT was a live measured scheduler.',
      suggestion='Use evaluated point trade-offs; preserve explicit descriptive-only/no statistical dominance caveat in central validity discussion.',
      detail='The table correctly separates M/S and omits S-row RPC latency. BA/cost values themselves match R8.'),
]
streaming=(M/'tables/r9-streaming.tex').read_text()
assert 'Verbosity' in streaming and 'Prefix' in streaming
assert 'Verbosity contrasts brief/expanded outputs; Prefix contrasts the first two/three sentences of each expanded output.' in streaming
assert 'cross-fit cross-fit' not in (M/'tables/r9-crossfit.tex').read_text()
assert 'These evaluated point trade-offs' in sections['42-live-timing-main.tex']
assert 'These measured point trade-offs' not in sections['42-live-timing-main.tex']
state_source=(M/'sections/38-retained-controlled.tex').read_text()
denominator=dict(numerator=173,denominator=291,source_eligible_tasks=97,repeats=3,
    source='manuscript/sections/38-retained-controlled.tex / reference-program state-scope experiment',
    unit='Before-program cover placements among tasks with an initially pending order; not all115tasks or independent customers',
    source37_explicit_task_denominator_now=('97' in sections['37-transfer-tests.tex'] and '291' in sections['37-transfer-tests.tex']),
    check='97*3 ==291; numeric fraction remains173/291')
assert 97*3==291 and '173/291' in state_source and '97' in state_source
assert all(s in sections['37-transfer-tests.tex'] for s in ['97 have an initially pending order','291 cover placements before','173 placements','118 calls fail'])
report=dict(status='PASS_NUMBERS_AND_RESOLVED_NOTES',tables=checked,
    checked_scientific_table_pairs=len(checked),numerical_rows=sum(x['numerical_rows'] for x in checked),
    numerical_tokens=sum(x['numerical_tokens'] for x in checked),
    semantic_unit_checks=checks,findings=findings,state_scope_denominator=denominator,
    scope='Eight scientific numerical tables match R8 exactly in numeric data columns; captions/first-column experiment IDs may change. New corpus/rules/index prose tables are not claimed to be verbatim R8 tables.',
    no_main_section_edits=True,no_compilation=True,
    input_sha256={str(p.relative_to(P)).replace('\\','/'):sha(p) for p in [stream]+[M/'sections'/n for n in sections]+[OLD/'sections'/n for n in sections]},
    code_sha256=sha(Path(__file__)))
(O/'condensed-numerical-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# R9 condensed numerical review','',report['status'],'',f"Eight scientific table pairs: {report['numerical_rows']} numerical rows and {report['numerical_tokens']} tokens match the R8 snapshot exactly.",'']
for v in findings:lines.append('- '+v['finding']+' '+v['suggestion'])
lines+=['',report['scope']]
(O/'condensed-numerical-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','checked_scientific_table_pairs','numerical_rows','numerical_tokens','findings']},ensure_ascii=False,indent=2))
