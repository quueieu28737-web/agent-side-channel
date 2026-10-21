"""Read-only verification of R3 predictions, intervals, holdout audit and tables."""
import hashlib
import json
from pathlib import Path
import numpy as np
import reanalyze as a
import make_tables as t
HERE=Path(__file__).resolve().parent
def load(name): return json.loads((HERE/name).read_text(encoding="utf-8"))
def main():
    preds=load("out_of_fold_predictions.json")
    assert [p["id"] for p in preds]==list(range(len(preds)))
    stats={}
    for p in preds:
        assert len(p["units"])==len(p["scores"])==len(p["predictions"])==345
        assert len({u["task"] for u in p["units"]})==115
        stats[p["id"]]=a.distributions(p["units"],p["scores"],p["predictions"])
    e6=load("e6_dispatch_results.json")
    e7=load("e7_network_results.json")["results"]
    assert len(e6)==16 and len(e7)==24
    for r in e6+e7:
        arrays=[]
        for attack in r["attackers"].values():
            ba,auc=stats[attack["prediction_id"]]
            assert np.allclose(ba[0],attack["ba"],rtol=0,atol=1e-12)
            assert np.allclose(auc[0],attack["auroc"],rtol=0,atol=1e-12)
            assert np.allclose(np.nanquantile(ba[1:],[.025,.975]),attack["ba_ci95"],rtol=0,atol=1e-12)
            arrays.append((ba,auc))
        for k,key in enumerate(("ba","auroc")):
            suite=np.nanmax([z[k] for z in arrays],axis=0)
            assert np.allclose(suite[0],r["best_"+key],rtol=0,atol=1e-12)
            assert np.allclose(np.nanquantile(suite[1:],[.025,.975]),r["best_"+key+"_ci95"],rtol=0,atol=1e-12)
        assert r["criterion"]==a.criterion(r["best_ba"],r["best_ba_ci95"],r["best_auroc"])
    old6=json.loads((a.R2/"e6_dispatch_results.json").read_text())
    old7=json.loads((a.R2/"e7_network_results.json").read_text())["results"]
    for new,old in zip(e6+e7,old6+old7):
        assert new["target"]==old["target"] and new["cover"]==old["cover"]
        assert np.isclose(new["best_ba"],old["best_ba"],rtol=0,atol=1e-12)
    identity=load("identity_and_calibration.json")
    assert identity==a.identity_and_calibration()
    for r in identity["request_only_grouped_oof"]:
        assert r["calls"]==len(r["predictions"])==582
    for target in ("cancel","return"):
        assert set(tid for f in identity["calibration_audit"] if f["target"]==target for tid in f["overflow_tasks"])=={22,28,40,67,87}
    for cover in {r["cover"] for r in e7}:
        for frame in {r["framing"] for r in e7}:
            cells=[r for r in e7 if r["cover"]==cover and r["framing"]==frame]
            assert len(cells)==2
            assert not all(r["criterion"]=="meets_evaluated_suite_criterion" for r in cells)
    for name,content in t.tables().items():
        assert (t.TAB/name).read_text(encoding="utf-8")==content,name
    source=load("input_hashes.json")
    for name,digest in source.items():
        assert hashlib.sha256((a.R2/name).read_bytes()).hexdigest()==digest,name
    print(json.dumps({"status":"R3_PASS","saved_prediction_sets":len(preds),"e6_cells":16,"e7_cells":24,
                      "identity_calls_per_split":582,"bootstrap_draws":2000,"tables":4,
                      "raw_input_hashes":len(source),"new_model_calls":0},indent=2))
if __name__=="__main__": main()
