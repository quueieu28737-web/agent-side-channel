"""Add paired program contrasts and equivalence scope to full-cohort tables."""
from pathlib import Path
import importlib.util,json,sys
HERE=Path(__file__).resolve().parent;P=HERE.parents[1]
spec=importlib.util.spec_from_file_location('previous_tables',P/'provenance/main-690/build_tables.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def sources():
    tables=old.sources();d=json.loads((HERE/'paired_program_results.json').read_text())
    assert d['status']=='PAIRED_PROGRAM_CONTRAST_AND_PROJECTION_CHECK_PASS'
    points={(r['prompt'],r['target']):r for r in d['contrasts']}
    def ci(arm,target):
        r=points[arm,target];return old.ci(r['difference'],r['ci95'])
    foot=(r'\par\smallskip\raggedright \textbf{Paired joint-minus-raw BA differences (percentage points):} baseline cancellation '+ci('baseline','cancel')+', return '+ci('baseline','return')+r'. These post hoc contrasts use the same customer draws and reselect the attack-suite maximum in each condition. Joint = online shadow cover plus constant framing; padding/shape ablations use baseline trajectories. Ratios use raw transport within each prompt. Shadow isolation preserves the logical planner transcript; the four program conditions replay actual LLM trajectories over local TLS~1.2. Full methods, intervals and prompt contrasts: Supplement S14.')
    s=tables['tables/r4-primary.tex'];start=s.index(r'\par\smallskip\raggedright');end=s.index(r'\end{table*}',start)
    tables['tables/r4-primary.tex']=s[:start]+foot+'\n'+s[end:]
    s=tables['tables/r4-supp.tex']
    oldtext='Shadow calls execute on a cloned initial database, with observations hidden from the planner. Real calls remain unchanged. Each trajectory is reused across program conditions, preserving reward by construction. The experiment measures call and byte costs; online delay and feedback-induced behavior require an interactive evaluation. A byte-transparent relay captures TLS~1.2 loopback replay of actual model-generated requests and sandbox responses.'
    newtext=r'''Shadow calls execute on isolated cloned state; their observations are suppressed and real calls/responses pass through unchanged. For deterministic tools with no timing-dependent side effects, projecting away cover gives the same planner-visible history under all program conditions. The replay therefore isolates transport intervention on the same realized actions, with reward preserved by the isolation invariant. All 690 real-call projections agree across the 2,760 saved sessions. Online means scheduling from past calls; interactive wall-clock delay and shared-resource feedback remain outside this replay measurement. A byte-transparent relay captures actual serialized requests and sandbox responses over local TLS~1.2.'''
    assert oldtext in s;s=s.replace(oldtext,newtext)
    heading=r'\subsection{Interpretation and reproducibility}'
    rows=[('baseline' if arm=='baseline' else 'rules')+' & '+target+' & '+ci(arm,target) for arm in ('baseline','rules') for target in ('cancel','return')]
    tab=old.table('llr',r'Prompt & Target & Joint minus raw BA [95\% CI], pp',rows,r'Post hoc paired program contrasts. The fixed attack suite is re-maximized under each condition within each common customer-bootstrap draw. Original predictions and the predeclared absolute criterion are unchanged.')
    s=s.replace(heading,tab+'\n\n'+heading)
    oldtext=r'Baseline joint upper bounds are 60.6\%/65.5\%. Rules-plus-joint return BA is 60.6\%; its paired contrast includes zero, as does the reward contrast.'
    newtext=r'Baseline joint upper bounds are 60.6\%/65.5\%, leaving the absolute-threshold conclusion inconclusive. The full-sample suite maximum equals the 50\% majority baseline; several fitted attacks make heterogeneous predictions whose customer-resampled BA can exceed 50\%. With only five cancellation-positive and seven return-positive customers, reselecting the maximum within each draw yields wider intervals. This mechanism does not imply a universal 10-point resolution floor or prove absence of residual population signal. The paired reduction intervals above exclude zero. Rules-plus-joint return BA is 60.6\%; its rules-minus-baseline contrast includes zero, as does the reward contrast.'
    assert oldtext in s;s=s.replace(oldtext,newtext)
    s=s.replace('measured workflow compliance','mechanical adherence to the two read-order rules')
    s=s.replace(r'Measured workflow compliance (\% with customer-cluster interval). These checks cover the two specified rules.',r'Mechanical adherence to the two prompt-specified read-order rules (\% with customer-cluster interval).')
    s=s.replace('Rules improve measured workflow compliance','Rules improve mechanical rule adherence')
    s=s.replace('The paired reduction intervals above exclude zero.','The paired reduction intervals above exclude zero. Supplement S16 adds a task-permutation reference; the primary intervals remain clustered by customer.')
    tables['tables/r4-supp.tex']=s
    return tables
def main():
    for name,s in sources().items():
        p=P/'manuscript'/name
        if '--check' in sys.argv:assert p.read_bytes()==s.encode('utf-8'),name
        else:p.write_text(s,encoding='utf-8',newline='\n')
    print('FULL_COHORT_TABLES_AND_PAIRED_CONTRASTS_MATCH')
if __name__=='__main__':main()
