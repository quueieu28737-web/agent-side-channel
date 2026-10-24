import argparse,joblib,platform
from r7common import *
import adapters
from learners import tabular,feature,SequenceAttack,sequence

def prepare():
    assert not (HERE/'freeze.json').exists(),'Do not overwrite a frozen experiment'
    tr=captures('train');cal=adapters.fit(tr);write(HERE/'calibration.json',cal)
    for part,source in [('train',tr),('test',captures('test'))]:
        out=[adapters.measured(r) for r in source]
        for r in source:
            if r['condition']=='raw':out.extend(adapters.transform(r,c,cal) for c in SIMULATED)
        out.sort(key=lambda r:(r['prompt'],r['condition'],r['task'],r['repeat']))
        assert len(out)==(414 if part=='train' else 276)*len(CONDITIONS)
        save_rows(HERE/(part+'.zip'),out)
    write(HERE/'freeze.json',{'utc':now(),'scope':'post_hoc_existing_cohort','seed':SEED,'conditions':CONDITIONS,
       'source_sha256':source_hashes(),'protocol_sha256':sha(HERE/'PROTOCOL.md'),
       'r6_captures_sha256':sha(R6/'captures.zip'),'calibration_sha256':sha(HERE/'calibration.json'),
       'data_sha256':{p:sha(HERE/(p+'.zip')) for p in ('train','test')},
       'environment':{'python':platform.python_version(),'platform':platform.platform(),'torch':__import__('torch').__version__,'numpy':np.__version__,'sklearn':__import__('sklearn').__version__},
       'test_previously_analyzed':True})
    print('PREPARED',len(CONDITIONS),flush=True)

def fit():
    frozen=read(HERE/'freeze.json');assert frozen['source_sha256']==source_hashes()
    assert not (HERE/'fit_complete.json').exists(),'Already fitted'
    rr=rows('train');md=HERE/'models';md.mkdir(exist_ok=True)
    for arm in ('baseline','rules'):
        for cond in CONDITIONS:
            rs=[r for r in rr if r['prompt']==arm and r['condition']==cond];X=[feature(r) for r in rs]
            for target in ('cancel','return'):
                name='|'.join((arm,cond,target));path=md/(name.replace('|','-')+'.joblib')
                if path.exists():continue
                y=np.array([r['has_'+target] for r in rs]);models=tabular()
                for m in models.values():m.fit(X,y)
                models['D2_sequence_CNN']=SequenceAttack().fit(rs,y)
                joblib.dump({'models':models,'majority':int(y.mean()>=.5),'units':[key(r) for r in rs],
                    'customers':sorted({r['user'] for r in rs}),'freeze_sha256':sha(HERE/'freeze.json')},path,compress=3)
                print('FIT',name,flush=True)
    write(HERE/'fit_complete.json',{'utc':now(),'freeze_sha256':sha(HERE/'freeze.json'),
         'models':{p.name:sha(p) for p in sorted(md.glob('*.joblib'))},'source_sha256':source_hashes()})

def model(name):
    p=HERE/'models'/name
    if p.exists():return joblib.load(p)
    import io
    with zipfile.ZipFile(HERE/'models.zip') as z:return joblib.load(io.BytesIO(z.read(name)))

def predict():
    receipt=read(HERE/'fit_complete.json');assert receipt['source_sha256']==source_hashes()
    rr=rows('test');old=read(R6/'predictions.json');out={}
    for arm in ('baseline','rules'):
        for cond in CONDITIONS:
            rs=[r for r in rr if r['prompt']==arm and r['condition']==cond];X=[feature(r) for r in rs]
            for target in ('cancel','return'):
                k='|'.join((arm,cond,target));pack=model(k.replace('|','-')+'.joblib')
                assert not set(pack['customers'])&{r['user'] for r in rs}
                scores={'majority':{'scores':[pack['majority']]*len(rs),'predictions':[pack['majority']]*len(rs)}}
                for name,m in pack['models'].items():
                    s=m.predict_proba(rs if name=='D2_sequence_CNN' else X)[:,1]
                    scores[name]={'scores':s.tolist(),'predictions':(s>=.5).astype(int).tolist()}
                if cond in MEASURED:
                    legacy=old['|'.join((arm,cond,'suite',target))];idx={v:i for i,v in enumerate(legacy['units'])}
                    order=[idx[key(r)] for r in rs]
                    for name,v in legacy['models'].items():scores['E13/'+name]={kk:[vv[i] for i in order] for kk,vv in v.items()}
                    assert [legacy['labels'][i] for i in order]==[r['has_'+target] for r in rs]
                out[k]={'units':[key(r) for r in rs],'customers':[r['user'] for r in rs],
                        'labels':[r['has_'+target] for r in rs],'models':scores,'cnn_test_truncated':sequence(rs)[1]}
            print('SCORED',arm,cond,flush=True)
    return out

def summarize(pred):
    rr=rows('test');cells={};cost={}
    for k,u in pred.items():
        w=r6.weights(u['customers']);bs=[];aus=[];details={}
        for name,v in u['models'].items():
            b,a=r6.metric_draws(u['labels'],v['scores'],v['predictions'],w);bs.append(b);aus.append(a)
            details[name]={'ba':float(b[0]),'auroc':float(a[0])}
        b=np.nanmax(bs,axis=0);a=np.nanmax(aus,axis=0)
        cells[k]={'ba':r6.brief(b),'auroc':r6.brief(a),'attackers':details,'suite_size':len(details),
                  'criterion':bool(np.nanquantile(b[1:],.975)<.60 and a[0]<.65),
                  'strongest_ba':[n for n,v in details.items() if abs(v['ba']-b[0])<1e-12],
                  'cnn_test_truncated':u['cnn_test_truncated']}
    for arm in ('baseline','rules'):
        base=[r for r in rr if r['prompt']==arm and r['condition']=='raw']
        for cond in CONDITIONS:
            units=[r for r in rr if r['prompt']==arm and r['condition']==cond]
            cost[arm+'|'+cond]={'wire_ratio':sum(r['wire_bytes'] for r in units)/sum(r['wire_bytes'] for r in base),
                'call_ratio':sum(r['calls'] for r in units)/sum(r['calls'] for r in base),
                'last_real_p95_ms':float(np.quantile([r['last_real_ms'] for r in units],.95)),
                'traffic_p95_ms':float(np.quantile([r['traffic_ms'] for r in units],.95)),
                'evidence':units[0]['evidence'],'ap_gap_caps':sum(r.get('integrity',{}).get('ap_gap_caps',0) for r in units)}
    return {'scope':'post_hoc_existing_690_trajectories','cells':cells,'resources':cost,
            'fit_sha256':sha(HERE/'fit_complete.json'),'protocol_sha256':sha(HERE/'PROTOCOL.md')}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','fit','evaluate','reproduce']);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='fit':fit()
    else:
        preds=predict();res=summarize(preds)
        if a.action=='reproduce':
            assert preds==read(HERE/'predictions.json');assert res==read(HERE/'results.json');print('EXACT_REPRODUCTION_PASS')
        else:
            assert not (HERE/'results.json').exists();write(HERE/'predictions.json',preds);write(HERE/'results.json',res)
