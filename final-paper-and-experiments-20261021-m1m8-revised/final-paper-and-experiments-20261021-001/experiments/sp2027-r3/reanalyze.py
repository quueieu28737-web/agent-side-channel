"""Post-review reanalysis of saved R2 observations; no new model or TLS runs.
Python 3.12, numpy 2.5.4, scikit-learn 1.9.0. Run with -B.
All classifiers/splits are R2's fixed suite. Confidence intervals are conditional
on saved out-of-fold predictions: training/search uncertainty is not included.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import importlib.util
import hashlib
import json
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
R2 = HERE.parent / "sp2027-r2"
spec = importlib.util.spec_from_file_location("r2_eval", R2 / "e67_eval.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CACHE = {}
PREDICTIONS = []

def write(path, value):
    path.write_text(json.dumps(value, indent=1) + "\n", encoding="utf-8", newline="\n")

def distributions(units, scores, preds, n=2000):
    tids = sorted(set(u["task"] for u in units))
    lookup = {t:i for i,t in enumerate(tids)}
    groups = np.array([lookup[u["task"]] for u in units])
    y = np.array([u["y"] for u in units])
    p = np.array(preds); s = np.array(scores)
    picks = np.random.default_rng(m.SEED).choice(len(tids), (n, len(tids)))
    wt = np.zeros((n, len(tids)))
    np.add.at(wt, (np.repeat(np.arange(n),len(tids)), picks.ravel()), 1)
    w = np.vstack((np.ones(len(y)), wt[:,groups]))
    pos = y == 1; neg = y == 0
    np_ = w[:,pos].sum(1); nn = w[:,neg].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ba = .5*((w[:,pos]*(p[pos]==1)).sum(1)/np_ +
                 (w[:,neg]*(p[neg]==0)).sum(1)/nn)
        order = np.argsort(s, kind="stable"); ss = s[order]
        wn = w[:,order]*neg[order]; wp = w[:,order]*pos[order]
        padded = np.column_stack((np.zeros(len(w)), np.cumsum(wn,axis=1)))
        starts = np.searchsorted(ss,ss,side="left")
        ends = np.searchsorted(ss,ss,side="right")
        below = padded[:,starts]; equal = padded[:,ends]-below
        auc = (wp*(below+.5*equal)).sum(1)/(np_*nn)
    return ba, auc

def boot(units, scores, preds, n=2000):
    ba, auc = distributions(units, scores, preds, n)
    pid = len(PREDICTIONS)
    PREDICTIONS.append({"id":pid, "units":units,
                        "scores":np.asarray(scores).tolist(),
                        "predictions":np.asarray(preds).tolist()})
    res = {"prediction_id":pid, "ba":float(ba[0]),
           "ba_ci95":np.nanquantile(ba[1:],[.025,.975]).tolist(),
           "auroc":float(auc[0]),
           "auroc_ci95":np.nanquantile(auc[1:],[.025,.975]).tolist()}
    CACHE[pid] = (ba,auc)
    return res

def summarize(res):
    # Identical resampled task indices for every attacker in this cell.
    ba = np.nanmax([CACHE[v["prediction_id"]][0] for v in res.values()],axis=0)
    auc = np.nanmax([CACHE[v["prediction_id"]][1] for v in res.values()],axis=0)
    best = max(res, key=lambda k:res[k]["ba"])
    return {"best_attacker":best, "best_ba":float(ba[0]),
            "best_ba_ci95":np.nanquantile(ba[1:],[.025,.975]).tolist(),
            "best_auroc":float(auc[0]),
            "best_auroc_ci95":np.nanquantile(auc[1:],[.025,.975]).tolist(),
            "interval_method":"task bootstrap of maximum over fixed attack suite",
            "criterion":criterion(float(ba[0]), np.nanquantile(ba[1:],[.025,.975]), float(auc[0]))}

def criterion(ba, ci, auc):
    if ci[0] > .60: return "above_threshold"
    if ci[1] < .60 and auc < .65: return "meets_evaluated_suite_criterion"
    return "inconclusive"

def rule(units, fs, y, counts_fn):
    sc=np.zeros(len(y)); pr=np.zeros(len(y),int)
    for k,(tr,te) in enumerate(fs):
        ctr=np.array(counts_fn(k,tr)); cte=np.array(counts_fn(k,te))
        best=(-1,0)
        for th in range(int(ctr.max())+2):
            pred=ctr>=th
            b=.5*(np.mean(pred[y[tr]==1])+np.mean(~pred[y[tr]==0]))
            if b>best[0]: best=(b,th)
        sc[te]=cte; pr[te]=cte>=best[1]
    return boot(units,sc,pr)

def identity_and_calibration():
    sessions=json.loads((R2/"e6_sessions.json").read_text())
    records=json.loads((R2/"e7_records.json").read_text())
    first=min(s["seed"] for s in sessions)
    S={s["task"]:s for s in sessions if s["cover"]=="none" and s["seed"]==first}
    R={(r["task"],r["framing"]):r["records"] for r in records
       if r["cover"]=="none" and r["seed"]==first}
    result=[]; calibration=[]
    # Match R2's 345-unit split definition before reducing to one seed per task.
    tasks=sorted(S); seeds=sorted(set(s["seed"] for s in sessions))
    for target,(lab,_) in m.TARGETS.items():
        units=[{"task":t,"seed":s,"y":S[t][lab]} for t in tasks for s in seeds]
        fs,_=m.folds(units)
        for frame in ("raw","bucket1024","const"):
            correct=basecorrect=total=0; calls=[]
            for fold,(tr,te) in enumerate(fs):
                train=sorted(set(units[i]["task"] for i in tr))
                test=sorted(set(units[i]["task"] for i in te))
                assert not set(train)&set(test)
                mapping=defaultdict(Counter); freq=Counter()
                for t in train:
                    for c,ex in zip(S[t]["calls"],m.exchanges(R[t,frame])):
                        mapping[ex[0]][c["name"]]+=1; freq[c["name"]]+=1
                majority=freq.most_common(1)[0][0]
                decoder={sz:cs.most_common(1)[0][0] for sz,cs in mapping.items()}
                for t in test:
                    for c,ex in zip(S[t]["calls"],m.exchanges(R[t,frame])):
                        pred=decoder.get(ex[0],majority)
                        correct+=pred==c["name"]; basecorrect+=majority==c["name"];total+=1
                        calls.append({"task":t,"fold":fold,"truth":c["name"],"predicted":pred,"baseline":majority})
            result.append({"target_stratification":target,"framing":frame,
                           "calls":total,"accuracy":correct/total,
                           "training_majority_accuracy":basecorrect/total,"predictions":calls})
        for fold,(tr,te) in enumerate(fs):
            train=sorted(set(units[i]["task"] for i in tr)); test=sorted(set(units[i]["task"] for i in te))
            counts={t:Counter(c["name"] for c in S[t]["calls"]) for t in tasks}
            verbs=sorted(set(v for c in counts.values() for v in c))
            tmpl={v:max(counts[t][v] for t in train) for v in verbs}
            overflow=[t for t in test if any(counts[t][v]>tmpl[v] for v in verbs)]
            calibration.append({"target":target,"fold":fold,"training_tasks":train,"test_tasks":test,
                                "training_only_shape_template":tmpl,"overflow_tasks":overflow})
    return {"request_only_grouped_oof":result,
            "calibration_audit":calibration,
            "scope":"Template feasibility audit only; no train-only defense effectiveness rerun."}

def check_bootstrap():
    rng=np.random.default_rng(17)
    units=[{"task":i,"y":i%2} for i in range(15) for j in range(1+i%3)]
    s=rng.integers(0,7,len(units))/6; p=(s>=.5).astype(int)
    a=m.cluster_boot(units,s,p,2000)
    ba,auc=distributions(units,s,p,2000)
    b={"ba":ba[0],"ba_ci95":np.nanquantile(ba[1:],[.025,.975]),
       "auroc":auc[0],"auroc_ci95":np.nanquantile(auc[1:],[.025,.975])}
    for k in a: assert np.allclose(a[k],b[k],atol=1e-12,rtol=0),k

def main():
    write(HERE/"input_hashes.json", {name:hashlib.sha256((R2/name).read_bytes()).hexdigest() for name in ("e6_sessions.json","e7_records.json","e7_meta.json","PREREGISTRATION.json","PREREGISTRATION_OUTCOMES.json")})
    check_bootstrap()
    m.cluster_boot=boot; m.summarize=summarize; m.rule=rule
    with tempfile.TemporaryDirectory() as tmp:
        D=Path(tmp)
        for name in ("e6_sessions.json","e7_records.json","e7_meta.json"):
            shutil.copyfile(R2/name,D/name)
        m.main(D)
        for name in ("e6_dispatch_results.json","e7_network_results.json"):
            data=json.loads((D/name).read_text())
            if name.startswith("e7"):
                data["in_sample_tool_purity_diagnostic"]=data.pop("tool_identification")
            write(HERE/name,data)
    write(HERE/"out_of_fold_predictions.json",PREDICTIONS)
    write(HERE/"identity_and_calibration.json",identity_and_calibration())
    import sklearn,sys
    write(HERE/"run_metadata.json",{"python":sys.version,"numpy":np.__version__,
          "sklearn":sklearn.__version__,"bootstrap_draws":2000,"seed":m.SEED,
          "analysis":"post-review; not preregistered","new_model_calls":0,"new_tls_captures":0,
          "interval_scope":"Percentile intervals of the suite maximum, conditional on fixed OOF predictions. No retraining, feature/search uncertainty, or unknown attacks."})
    print("R3_REANALYSIS_COMPLETE",flush=True)

if __name__=="__main__": main()
