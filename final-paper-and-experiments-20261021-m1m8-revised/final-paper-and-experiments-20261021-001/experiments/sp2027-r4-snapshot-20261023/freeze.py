"""Freeze the task split and protocol BEFORE formal model data collection."""
import datetime
from collections import Counter
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from common import *

def main():
    ns, tools, base, tasks = load()
    labels = [int(any(a.name=='cancel_pending_order' for a in t.actions)) +
              2*int(any(a.name=='return_delivered_order_items' for a in t.actions)) for t in tasks]
    groups = [t.user_id for t in tasks]
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20261021).split(np.zeros(len(tasks)), labels, groups))
    test = sorted(int(x) for x in set(folds[0][1]) | set(folds[1][1]))
    train = sorted(set(range(len(tasks)))-set(test))
    assert not {groups[t] for t in train}&{groups[t] for t in test}
    obj = {'train':train, 'test':test, 'grouping':'customer ID; repeated tasks remain together',
           'seed':20261021, 'joint_label_counts':{s:dict(Counter(str(labels[t]) for t in ids)) for s,ids in [('train',train),('test',test)]},
           'pilot_tasks':train[:2], 'labels':labels,
           'prior_exposure':'All 115 public tasks were used in earlier manuscript development; this is a new frozen split, not an untouched external benchmark.'}
    target=HERE/'split.json'
    if target.exists():
        assert read(target)==obj, 'Refuse to replace existing split'
    else:
        write(target,obj)
    protocol = {'version':4, 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'model':MODEL, 'interface':'Persistent Codex app-server with fresh ephemeral no-environment context per structured next-action call; ChatGPT authentication',
        'reasoning_effort':'low', 'temperature':'not exposed by CLI; not claimed fixed',
        'repeats':REPEATS, 'max_steps':MAX_STEPS, 'prompts':PROMPTS, 'rules':RULES,
        'conditions':['baseline/raw','rules/raw','baseline/shape_const','rules/shape_const'],
        'secondary_conditions':['baseline/padding_only','rules/padding_only','baseline/shape_only','rules/shape_only'],
        'split_sha256':sha(target),
        'defense':'Shared shape template and donor action pools fitted to both prompt arms of TRAIN episodes only. Request cap = ceil((max train request bytes+4)/256)*256; response cap = ceil((train response p95+4)/1024)*1024. Freeze before test collection. Include training donor responses in cap calibration.',
        'overflow':'Never truncate/drop real calls. Exceeding counts pass through and are flagged. Oversize messages round up to next 1024-byte bucket and are flagged. No test-driven adaptation.',
        'shadow':'Cover actions execute only on a copy of initial sandbox state, invisible to planner. Per-prompt trajectory may be reused across program defense conditions. TLS is measured loopback replay, not live provider latency.',
        'attackers':['training-majority','D0_gboost','D2_logreg','D2_gboost','D2_count_rule','network_decode_gboost','network_decode_count_rule'],
        'attacker_parameters':'R2 fixed model settings; rule threshold candidates training only; decoder trained on defended training calls only. Public API schemas define verb vocabulary.',
        'targets':['reference cancellation intent','reference return intent'],
        'primary_metrics':['BA','AUROC','native task reward','model failure/status','template and framing overflow','application-record wire bytes','tool calls'],
        'statistics':'2000 common customer-cluster-bootstrap draws retaining all customer tasks and repeats, task-weighted point estimates, suite maximum recomputed each draw; task-paired prompt differences. Report single-class discarded draws. Conditional on trained attackers; no training uncertainty or unknown attacks. Test set once, no outcome-based tuning.',
        'criterion':'Descriptive only: suite BA upper CI <0.60 and point AUROC <0.65 for BOTH targets. Failing or inconclusive results remain included.',
        'failures':'Keep max-step, protocol-invalid and tool failures as observations. Infrastructure failures resume from per-episode cache and are logged; no silent complete-case filtering.',
        'independence':'Fresh inference cache namespace per task x repeat x prompt x role; repeat IDs are not provider random seeds.',
        'external_validation':'No independent human coding or external replication is claimed.'}
    if not (HERE/'protocol.json').exists(): write(HERE/'protocol.json',protocol)
    else:
        prev=read(HERE/'protocol.json');protocol['created_utc']=prev['created_utc'];assert prev==protocol
    print(json.dumps({k:obj[k] for k in ('train','test','pilot_tasks','joint_label_counts')},indent=1))

if __name__=='__main__': main()
