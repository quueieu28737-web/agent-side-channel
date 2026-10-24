"""Fit only on 414 training episodes, freeze models, then evaluate 276 test episodes."""
import argparse
import datetime as dt
import zipfile
import io
from collections import defaultdict
import joblib
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from r6common import *
from features import features, local_features, cutpoint
import profile_attack

VIEWS=['size_order','timing_direction','joint']
CHECK=False

def save(path,obj):
    if CHECK:
        assert read(path)==obj, ('Recomputed output differs',path.name)
    else:
        write(path,obj)

def load_model(name):
    p=HERE/'models'/name
    if p.exists():return joblib.load(p)
    with zipfile.ZipFile(HERE/'models.zip') as z:
        return joblib.load(io.BytesIO(z.read('models/'+name)))

def model_sha(name):
    p=HERE/'models'/name
    if p.exists():return sha(p)
    with zipfile.ZipFile(HERE/'models.zip') as z:
        return hashlib.sha256(z.read('models/'+name)).hexdigest()

def captures(partition):
    root=HERE/'captures'/partition
    if root.exists():
        rows=[read(p) for p in sorted(root.glob('*.json'))]
    else:
        with zipfile.ZipFile(HERE/'captures.zip') as z:
            rows=[json.loads(z.read(n)) for n in sorted(z.namelist()) if n.startswith(f'captures/{partition}/')]
    assert len(rows)==(414 if partition=='train' else 276)*6
    return rows

def detector():
    return make_pipeline(DictVectorizer(sparse=False),RandomForestClassifier(
        n_estimators=80,max_depth=8,min_samples_leaf=5,class_weight='balanced',random_state=SEED,n_jobs=1))

def detector_data(rows, kind):
    X=[]; y=[]; groups=[]; spans=[]
    for r in rows:
        fs=local_features(r['records']);start=len(X)
        if kind=='flush':
            X.extend(fs)
            y.extend(int(t>=r['marks']['flush_start_ns']) for d,n,t in r['records'])
        else:
            # Each request is below a TLS fragment; validate one observed c2s record per send.
            indices=[i for i,(d,n,t) in enumerate(r['records']) if d==1]
            sends=r['client_send']
            assert len(indices)==len(sends)==len(r['requests'])
            req={q['id']:q for q in r['requests']}
            for i,s in zip(indices,sends):
                X.append(fs[i]); y.append(int(req[s['id']]['kind']=='cover'))
        groups.extend([r['user']]*(len(X)-start))
        spans.append((start,len(X)))
    return X,np.array(y),np.array(groups),spans

def classifier_models():
    return {
        'logistic':make_pipeline(DictVectorizer(sparse=False),StandardScaler(),LogisticRegression(
            C=1,class_weight='balanced',max_iter=3000,random_state=SEED)),
        'gboost':make_pipeline(DictVectorizer(sparse=False),GradientBoostingClassifier(
            n_estimators=100,random_state=SEED)),
        'forest':make_pipeline(DictVectorizer(sparse=False),RandomForestClassifier(
            n_estimators=200,min_samples_leaf=2,class_weight='balanced',random_state=SEED,n_jobs=1))}

def model_path(arm,cond,view,target):
    return HERE/'models'/f'{arm}-{cond}-{view}-{target}.joblib'

def train():
    assert not (HERE/'attacker_freeze.json').exists(), 'Models are already frozen; do not overwrite'
    rows=captures('train')
    assert all(r['status']=='complete' and r['response_equal'] and r['db_equal'] for r in rows)
    cuts={}; modelsdir=HERE/'models';modelsdir.mkdir(exist_ok=True)
    train_detector_receipts={}
    for cond in ('shadow_serial','shadow_parallel2'):
        units=[r for r in rows if r['condition']==cond]
        for kind in ('flush','cover'):
            X,y,groups,spans=detector_data(units,kind)
            model=detector();model.fit(X,y)
            joblib.dump(model,modelsdir/f'{cond}-{kind}.joblib',compress=3)
            if kind=='flush':
                # OOF preprocessing prevents training the intent learner on self-fitted segmentation.
                oof=np.zeros(len(y)); folds=[]
                for tr,te in GroupKFold(3).split(X,y,groups):
                    m=detector();m.fit([X[i] for i in tr],y[tr])
                    oof[te]=m.predict_proba([X[i] for i in te])[:,1]
                    folds.append({'train_customers':sorted(set(groups[tr])),'heldout_customers':sorted(set(groups[te]))})
                for r,(a,b) in zip(units,spans):cuts[key(r)+'-'+cond]=cutpoint(oof[a:b])
                train_detector_receipts[cond]={'folds':folds,'oof_ba':float(balanced_accuracy_score(y,oof>=.5)),
                    'oof_auc':float(roc_auc_score(y,oof))}
            print('FITTED_DETECTOR',cond,kind,len(y),flush=True)
    write(HERE/'training_cuts.json',{'cuts':cuts,'detectors':train_detector_receipts})
    for arm in ('baseline','rules'):
        for cond in CONDITIONS:
            units=[r for r in rows if r['prompt']==arm and r['condition']==cond]
            views=VIEWS+(['flush_stripped_joint'] if cond.startswith('shadow') else [])
            for view in views:
                X=[features(r['records'][:cuts[key(r)+'-'+cond]] if view=='flush_stripped_joint' else r['records'],view) for r in units]
                for target in ('cancel','return'):
                    y=np.array([r['has_'+target] for r in units]); fitted=classifier_models()
                    for model in fitted.values():model.fit(X,y)
                    pack={'models':fitted,'majority':int(y.mean()>=.5)}
                    if view=='size_order' and not cond.startswith('tunnel'):
                        pack['profile']=profile_attack.fit(units,target)
                    joblib.dump(pack,model_path(arm,cond,view,target),compress=3)
                print('FITTED_INTENT',arm,cond,view,flush=True)
    receipt={'fitted_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'frozen_sha256':sha(HERE/'frozen.json'),'train_complete_sha256':sha(HERE/'train_complete.json'),
             'source_sha256':{n:sha(HERE/n) for n in ('analyze.py','features.py','profile_attack.py')},
             'models':{p.name:sha(p) for p in sorted(modelsdir.glob('*.joblib'))},
             'training_cuts_sha256':sha(HERE/'training_cuts.json'),
             'test_captures_present_at_fit':(HERE/'test_complete.json').exists()}
    assert not receipt['test_captures_present_at_fit']
    write(HERE/'attacker_freeze.json',receipt)
    print('TRAINING_ATTACKERS_FROZEN',flush=True)

def weights(users,n=2000):
    groups=sorted(set(users));lookup={g:i for i,g in enumerate(groups)}
    indices=np.array([lookup[g] for g in users]);rng=np.random.default_rng(SEED)
    picks=rng.integers(0,len(groups),(n,len(groups)))
    counts=np.zeros((n,len(groups)),dtype=int)
    np.add.at(counts,(np.repeat(np.arange(n),len(groups)),picks.ravel()),1)
    return np.vstack((np.ones((1,len(users))),counts[:,indices]))

def metric_draws(y,scores,pred,w):
    y=np.asarray(y);s=np.asarray(scores);p=np.asarray(pred);pos=y==1;neg=y==0
    np_=w[:,pos].sum(1);nn=w[:,neg].sum(1)
    with np.errstate(invalid='ignore',divide='ignore'):
        ba=.5*((w[:,pos]*(p[pos]==1)).sum(1)/np_+(w[:,neg]*(p[neg]==0)).sum(1)/nn)
        order=np.argsort(s,kind='stable');ss=s[order]
        wn=w[:,order]*neg[order];wp=w[:,order]*pos[order]
        padded=np.column_stack((np.zeros(len(w)),np.cumsum(wn,axis=1)))
        starts=np.searchsorted(ss,ss,'left');ends=np.searchsorted(ss,ss,'right')
        auc=(wp*(padded[:,starts]+.5*(padded[:,ends]-padded[:,starts]))).sum(1)/(np_*nn)
    return ba,auc

def brief(a):
    return {'point':float(a[0]),'ci95':np.nanquantile(a[1:],[.025,.975]).tolist(),
            'invalid_draws':int(np.isnan(a[1:]).sum())}

def detector_metrics(y,p,groups):
    # Aggregate confusion counts by customer before resampling, avoiding huge record x draw arrays.
    unique=sorted(set(groups)); c=[]
    for g in unique:
        use=groups==g; yy=y[use]; pp=p[use]>=.5
        c.append([np.sum((yy==1)&pp),np.sum(yy==1),np.sum((yy==0)&~pp),np.sum(yy==0)])
    c=np.asarray(c);w=weights(unique);z=w@c
    with np.errstate(invalid='ignore',divide='ignore'):b=.5*(z[:,0]/z[:,1]+z[:,2]/z[:,3])
    return {'ba':brief(b),'auroc':float(roc_auc_score(y,p)),'records_or_calls':len(y),'customers':len(unique)}

def evaluate():
    frozen=read(HERE/'attacker_freeze.json')
    assert frozen['source_sha256']=={n:sha(HERE/n) for n in ('analyze.py','features.py','profile_attack.py')}
    assert all(model_sha(n)==h for n,h in frozen['models'].items())
    rows=captures('test'); cuts={};detresults={};detpred={}
    for cond in ('shadow_serial','shadow_parallel2'):
        units=[r for r in rows if r['condition']==cond]
        for kind in ('flush','cover'):
            X,y,groups,spans=detector_data(units,kind)
            m=load_model(f'{cond}-{kind}.joblib');p=m.predict_proba(X)[:,1]
            detresults[cond+'-'+kind]=detector_metrics(y,p,groups)
            detpred[cond+'-'+kind]={'y':y.tolist(),'scores':p.tolist(),'customers':groups.tolist(),
                                  'units':[key(r) for r in units],'spans':spans}
            if kind=='flush':
                for r,(a,b) in zip(units,spans):cuts[key(r)+'-'+cond]=cutpoint(p[a:b])
    save(HERE/'detector_predictions.json',detpred)
    cells={};predictions={};draws={}
    for arm in ('baseline','rules'):
        for cond in CONDITIONS:
            units=[r for r in rows if r['prompt']==arm and r['condition']==cond]
            w=weights([r['user'] for r in units])
            views=VIEWS+(['flush_stripped_joint'] if cond.startswith('shadow') else [])
            for view in views:
                X=[features(r['records'][:cuts[key(r)+'-'+cond]] if view=='flush_stripped_joint' else r['records'],view) for r in units]
                for target in ('cancel','return'):
                    k='|'.join((arm,cond,view,target));y=np.array([r['has_'+target] for r in units])
                    modelpack=load_model(model_path(arm,cond,view,target).name);maj=modelpack['majority']
                    output={'majority':(np.full(len(y),float(maj)),np.full(len(y),maj))}
                    for name,m in modelpack['models'].items():output[name]=(m.predict_proba(X)[:,1],m.predict(X))
                    if 'profile' in modelpack:output.update(profile_attack.predict(units,modelpack['profile']))
                    result={};bd=[];ad=[]
                    predictions[k]={'units':[key(r) for r in units],'customers':[r['user'] for r in units],
                                    'labels':y.tolist(),'models':{}}
                    for name,(s,p) in output.items():
                        ba,auc=metric_draws(y,s,p,w);bd.append(ba);ad.append(auc)
                        result[name]={'ba':brief(ba),'auroc':brief(auc)}
                        predictions[k]['models'][name]={'scores':s.tolist(),'predictions':p.tolist()}
                    b=np.nanmax(bd,axis=0);a=np.nanmax(ad,axis=0);draws[k]=b
                    cells[k]={'ba':brief(b),'auroc':brief(a),'models':result,
                              'meets_absolute_criterion':bool(np.nanquantile(b[1:],.975)<.60 and a[0]<.65)}
            print('EVALUATED',arm,cond,flush=True)
    # An adaptive observer can ignore timing or keep the unstripped trace.
    # The full suite therefore includes every declared view, not just the
    # classifier receiving all features in one vector.
    for arm in ('baseline','rules'):
        for cond in CONDITIONS:
            for target in ('cancel','return'):
                sourcekeys=['|'.join((arm,cond,v,target)) for v in VIEWS+(['flush_stripped_joint'] if cond.startswith('shadow') else [])]
                first=predictions[sourcekeys[0]]; y=np.array(first['labels']); w=weights(first['customers'])
                combined={}; bd=[]; ad=[]; details={}
                for sk in sourcekeys:
                    view=sk.split('|')[2]
                    for name,out in predictions[sk]['models'].items():
                        if name=='majority' and 'majority' in combined:continue
                        label='majority' if name=='majority' else view+'/'+name
                        combined[label]=out
                        ba,auc=metric_draws(y,out['scores'],out['predictions'],w)
                        bd.append(ba);ad.append(auc);details[label]={'ba':brief(ba),'auroc':brief(auc)}
                k='|'.join((arm,cond,'suite',target)); b=np.nanmax(bd,axis=0); a=np.nanmax(ad,axis=0)
                predictions[k]={**first,'models':combined}; draws[k]=b
                cells[k]={'ba':brief(b),'auroc':brief(a),'models':details,
                          'meets_absolute_criterion':bool(np.nanquantile(b[1:],.975)<.60 and a[0]<.65)}
    contrasts={}
    for arm in ('baseline','rules'):
        for target in ('cancel','return'):
            raw='|'.join((arm,'raw','suite',target))
            for cond in CONDITIONS:
                joint='|'.join((arm,cond,'suite',target));size='|'.join((arm,cond,'size_order',target))
                contrasts[joint+'-raw']=brief(draws[joint]-draws[raw])
                contrasts[joint+'-size']=brief(draws[joint]-draws[size])
    save(HERE/'predictions.json',predictions)
    save(HERE/'test_cuts.json',cuts)
    res={'cells':cells,'detectors':detresults,'contrasts':contrasts,'resources':resources(rows),
         'training_sessions':2484,'test_sessions':1656,'source_runs':690,
         'frozen_sha256':sha(HERE/'frozen.json'),'attacker_freeze_sha256':sha(HERE/'attacker_freeze.json'),
         'inference':'2000 paired customer bootstrap draws, conditional on fitted models; same known R4 cohort',
         'new_model_calls':0,'measurement':'new live local tool execution and real TLS arrival measurements'}
    save(HERE/'results.json',res)
    print('E13_EVALUATION_COMPLETE',flush=True)

def resources(rows):
    result={}
    for arm in ('baseline','rules'):
        raw={key(r):r for r in rows if r['prompt']==arm and r['condition']=='raw'}
        for cond in CONDITIONS:
            units=[r for r in rows if r['prompt']==arm and r['condition']==cond]
            calls=[];queues=[];service=[];first=[];finish=[];drain=[];late=[];native=[]
            for r in units:
                complete={x['id']:x['time_ns'] for x in r['completions']}
                real=[q for q in r['requests'] if q['kind']=='real']
                times=[complete[q['id']]-q['queued_ns'] for q in real if q['id'] in complete]
                calls.extend(x/1e6 for x in times)
                queues.extend((q['released_ns']-q['queued_ns'])/1e6 for q in r['requests'])
                service.extend((q['end_ns']-q['start_ns'])/1e6 for q in r['backend'])
                first.append(min((complete[q['id']] for q in real if q['id'] in complete),default=0)/1e6)
                finish.append(r['marks']['last_real_ns']/1e6);drain.append(r['finish_ns']/1e6)
                late.extend((s['time_ns']-s['deadline_ns'])/1e6 for s in r['client_send']+r['server_send'] if 'deadline_ns' in s)
                native.append(r['native_reward'] if r['response_equal'] and r['db_equal'] else 0)
            out={}
            for name,vals in (('real_call_ms',calls),('client_queue_ms',queues),('service_ms',service),
                              ('first_response_ms',first),('last_real_response_ms',finish),('traffic_finish_ms',drain),('slot_lateness_ms',late)):
                out[name]={'p50':float(np.median(vals)),'p95':float(np.quantile(vals,.95)),'max':float(max(vals))} if vals else None
            out.update(wire_ratio=sum(r['wire_bytes'] for r in units)/sum(raw[key(r)]['wire_bytes'] for r in units),
                       call_ratio=sum(len(r['requests']) for r in units)/sum(len(raw[key(r)]['requests']) for r in units),
                       sessions=len(units),failures=sum(r['status']!='complete' for r in units),
                       response_equal=sum(r['response_equal'] for r in units),db_equal=sum(r['db_equal'] for r in units),
                       preserved_native_reward=sum(native),total_native_reward=sum(r['native_reward'] for r in units),
                       deadline_misses_100ms=sum(x>100 for x in calls),
                       clock_scope='Tool RPC chain only: planner/user generation and WAN excluded')
            w=weights([r['user'] for r in units]);b=np.array([raw[key(r)]['marks']['last_real_ns']/1e6 for r in units])
            out['paired_mean_last_response_delta_ms']=brief(w@(np.array(finish)-b)/w.sum(1))
            result[arm+'|'+cond]=out
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['fit','evaluate']);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    CHECK=a.check
    train() if a.action=='fit' else evaluate()
