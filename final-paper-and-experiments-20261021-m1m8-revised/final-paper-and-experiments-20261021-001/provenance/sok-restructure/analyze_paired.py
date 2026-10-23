"""Post hoc paired program contrasts using frozen E9 predictions only.

Use the original 2,000 common customer-cluster draws. No refitting/model calls.
Also audit the real-call projection of every saved program condition.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,sys,warnings
import numpy as np
P=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
F=P/'experiments/sp2027-r4-full-20261023'
sys.path.insert(0,str(P/'experiments/sp2027-r3'))
import reanalyze as stats
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pred=read(F/'predictions.json');data=read(F/'results.json')
    cells=defaultdict(list)
    for p in pred:
        if p['view']=='network' and p['condition'] in ('raw','shape_const'):
            cells[p['prompt'],p['condition'],p['target']].append(p)
    maxima={};diagnostics=[]
    for key,ps in cells.items():
        assert all(p['units']==ps[0]['units'] for p in ps)
        draws=[]
        for p in ps:
            b,a=stats.distributions(p['units'],p['scores'],p['predictions'],2000)
            draws.append(b)
            if key[1]=='shape_const':
                diagnostics.append({'prompt':key[0],'target':key[2],'attacker':p['attacker'],'point_ba':float(b[0]),'nonconstant_predictions':len(set(p['predictions']))>1,'resampled_ba_range':[float(np.nanmin(b[1:])),float(np.nanmax(b[1:]))]})
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            m=np.nanmax(draws,axis=0)
        saved=next(x for x in data['results'] if (x['prompt'],x['condition'],x['target'],x['view'])==(*key,'network'))
        assert np.isclose(m[0],saved['suite_ba'])
        assert np.allclose(np.nanquantile(m[1:],[.025,.975]),saved['suite_ba_ci95'])
        maxima[key]=m
    contrasts=[]
    for arm in ('baseline','rules'):
        for target in ('cancel','return'):
            raw=next(p for p in cells[arm,'raw',target]);joint=next(p for p in cells[arm,'shape_const',target])
            assert raw['units']==joint['units']
            d=maxima[arm,'shape_const',target]-maxima[arm,'raw',target]
            contrasts.append({'prompt':arm,'target':target,'contrast':'joint minus raw network suite-maximum BA','difference':float(d[0]),'ci95':np.nanquantile(d[1:],[.025,.975]).tolist(),'valid_bootstrap_draws':int(np.isfinite(d[1:]).sum())})
    sessions=read(F/'sessions.json');groups=defaultdict(list)
    for s in sessions:groups[s['prompt'],s['task'],s['repeat']].append(s)
    checked=0
    for key,ss in groups.items():
        assert {s['condition'] for s in ss}=={'raw','padding_only','shape_only','shape_const'}
        raw=next(s for s in ss if s['condition']=='raw')
        for s in ss:
            assert [c for c in s['calls'] if c['kind']=='real']==raw['calls'],key
            assert all(s[k]==raw[k] for k in ('native_reward','db_eq','status','episode_sha256')),key
            checked+=1
    out={'status':'PAIRED_PROGRAM_CONTRAST_AND_PROJECTION_CHECK_PASS','analysis_status':'Post hoc contrast requested during manuscript revision; original protocol and saved results unchanged.','seed':20261021,'bootstrap_draws':2000,'unit':'customer cluster; same draws for raw/joint; all tasks and repetitions retained; suite maximum recomputed per condition per draw','interval_scope':'Conditional on fitted attackers and recorded trajectories. Percentile intervals; no p-value or power claim.','contrasts':contrasts,'joint_attacker_diagnostics':diagnostics,'projection_check':{'episodes':len(groups),'sessions':checked,'checked':'Real-call name, kind, request/response byte lengths, error flag, source episode hash and native scoring fields are identical across program conditions. Exact serialized transcript preservation additionally follows from the frozen dispatcher append(dict(c,kind=real)) implementation and prior full verifier.'},'inputs':{n:sha(F/n) for n in ('predictions.json','results.json','sessions.json')},'frozen_statistics_sha256':sha(P/'experiments/sp2027-r3/reanalyze.py'),'frozen_dispatcher_sha256':sha(P/'experiments/sp2027-r4-snapshot-20261023/pretest-source/defense.py')}
    (HERE/'paired_program_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':out['status'],'contrasts':contrasts,'projection_check':out['projection_check']},indent=2))
if __name__=='__main__':main()
