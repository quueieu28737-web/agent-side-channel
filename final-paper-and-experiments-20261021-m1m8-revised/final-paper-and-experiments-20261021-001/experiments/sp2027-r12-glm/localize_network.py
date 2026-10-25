"""Oracle write-exchange localization: actual TLS replay, fixed train/test learners."""
from common import *
from network_replay import episodes, tlslab, frame
from evaluate_network import ev,stats,predict_model,decoder,decode,count_rule
import tempfile,numpy as np

def main():
    plan=read(HERE/'formal_plan.json'); results=[]; predictions=[]; sessions=[]
    allrows=episodes('train')+episodes('test'); ns,tools,base,tasks=load();verbs=sorted(tools)
    with tempfile.TemporaryDirectory(prefix='r12-localization-') as tmp:
        contexts=tlslab.make_contexts(Path(tmp),'1.2')
        for view in ('all','writes-only','writes-removed'):
            samples={p:[] for p in ('train','test')}
            for e in allrows:
                calls=[c for c in e['calls'] if view=='all' or ((c['name'] in ev.WRITES)==(view=='writes-only'))]
                ex=[(frame(c['req_text'],'raw',True,{}),frame(c['resp_text'],'raw',False,{})) for c in calls]
                records=tlslab.run_session(*contexts,ex) if ex else []
                s={k:e[k] for k in ('task','user','has_cancel','has_return')}
                s.update(view=view,calls=calls,records=records)
                samples['train' if e['task'] in plan['train'] else 'test'].append(s);sessions.append(s)
            tr=samples['train'];te=samples['test'];mapping=decoder(tr)
            Xtr=[ev.net_features(s['records']) for s in tr];Xte=[ev.net_features(s['records']) for s in te]
            dtr=[decode(s,mapping) for s in tr];dte=[decode(s,mapping) for s in te]
            for target,(label,verb) in ev.TARGETS.items():
                ytr=np.array([s[label] for s in tr]);units=[{'task':s['user'],'task_id':s['task'],'seed':0,'y':s[label]} for s in te]
                majority=int(ytr.mean()>=.5);attacks={'majority':(np.full(len(te),float(majority)),np.full(len(te),majority))}
                for model in ev.MODELS:
                    score=predict_model(Xtr,ytr,Xte,model);attacks['D2_'+model]=(score,(score>=.5).astype(int))
                score=predict_model([ev.disp_features(c,verbs) for c in dtr],ytr,[ev.disp_features(c,verbs) for c in dte],'gboost')
                attacks['network_decode_gboost']=(score,(score>=.5).astype(int))
                score,pred,th=count_rule([sum(c['name']==verb for c in cs) for cs in dtr],ytr,[sum(c['name']==verb for c in cs) for cs in dte])
                attacks['network_decode_count_rule']=(score,pred)
                bb=[];aa=[]
                for attacker,(score,pred) in attacks.items():
                    b,a=stats.distributions(units,score,pred,2000);bb.append(b);aa.append(a)
                    predictions.append({'view':view,'target':target,'attacker':attacker,'units':units,'scores':score.tolist(),'predictions':pred.tolist()})
                b=np.nanmax(bb,axis=0);a=np.nanmax(aa,axis=0)
                results.append({'view':view,'target':target,'suite_ba':float(b[0]),'suite_ba_ci95':np.nanquantile(b[1:],[.025,.975]).tolist(),'suite_auroc':float(a[0]),'attackers':list(attacks),'test_customers':len(set(s['user'] for s in te))})
    write(HERE/'localization_sessions.json',sessions)
    write(HERE/'localization_predictions.json',predictions)
    write(HERE/'localization_results.json',{'results':results,'scope':'Oracle selects exchanges by true write names; attackers see only replayed TLS record directions/lengths/order. Fixed R4 learners, not the expanded Sol cross-fit suite. Customer bootstrap conditional on fitted learners.'})

if __name__=='__main__':main()
