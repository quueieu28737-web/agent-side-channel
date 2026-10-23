"""Verify the immutable interim release, including original freezes and extra runs."""
import json,zipfile
from pathlib import PureWindowsPath
from collections import Counter
from hash_cache import install,verify_unchanged
install()
from common import *
from verify_r4 import verify

def main():
    a=read(HERE/'snapshot_amendment.json')
    original=read(HERE/'split.json');subset=read(HERE/'analysis_split.json')
    assert subset['train']==original['train'] and set(subset['test'])<=set(original['test'])
    eps=[read(p) for p in (HERE/'runs').glob('*/*/episode.json')]
    assert len(eps)==a['completed_episodes']==663
    counts=Counter(e['task'] for e in eps)
    assert subset['test']==[t for t in original['test'] if counts[t]==6]
    for rel,digest in a['source_episode_hashes'].items():assert sha(HERE/rel)==digest
    assert len(a['source_episode_hashes'])==663
    assert len({(e['prompt'],e['task'],e['repeat']) for e in eps})==663
    for manifest in ('runtime_manifest.json','pretest_analysis_manifest.json'):
        m=read(HERE/manifest)
        for name,digest in m['files'].items():
            parts=PureWindowsPath(name).parts
            if parts[0]=='sp2027-r4':
                p=HERE.joinpath(*parts[1:])
                if manifest.startswith('pretest'):p=HERE/'pretest-source'/parts[-1]
            else:p=EXP.joinpath(*parts)
            assert sha(p)==digest,(manifest,name)
    assert sha(HERE/'calibration.json')==read(HERE/'pretest_analysis_manifest.json')['calibration_sha256']
    for name,digest in read(HERE/'analysis_source_hashes.json').items():assert sha(HERE/name)==digest
    # Verify the declared amendment changes only cohort membership and validation.
    expected=(HERE/'pretest-source/evaluate.py').read_text().replace("split=read(HERE/'split.json');rows=","split=read(HERE/'analysis_split.json');rows=")
    expected=expected.replace('len(tasks)*len(REPEATS)*len(PROMPTS)*len(CONDITIONS)',"sum(len(split[p]) for p in ('train','test'))*len(REPEATS)*len(PROMPTS)*len(CONDITIONS)")
    assert expected==(HERE/'evaluate.py').read_text()
    expected=(HERE/'pretest-source/defense.py').read_text().replace("for tid in read(HERE/'split.json')[partition]:","for tid in read(HERE/'analysis_split.json')[partition]:")
    assert expected==(HERE/'defense.py').read_text()
    decisions=0
    fingerprint=inference_fingerprint()
    pretest_frozen=read(HERE/'pretest_analysis_manifest.json')['frozen_utc']
    for name in ('model-records-baseline.zip','model-records-rules.zip','additional-completed-records.zip'):
        with zipfile.ZipFile(HERE/name) as z:
            assert z.testzip() is None
            names=set(z.namelist())
            for n in names:
                if n.endswith('/request.json'):
                    q=json.loads(z.read(n));assert q['inference_fingerprint']==fingerprint
                    assert n[:-12]+'result.json' in names,n
                    decisions+=1
                if n.endswith('/result.json'):
                    r=json.loads(z.read(n))
                    assert r['inference_fingerprint']==fingerprint
                    # Protocol errors, if present, remain episodes rather than discarded trials.
                    if 'reported_model' in r:
                        assert r['reported_model']==r['requested_model']==MODEL
                        assert r['reasoning_effort']=='low' and r['instruction_sources']==[]
                    tid=int(n.split('/')[2].split('-')[1])
                    if tid in original['test']:
                        assert r['collected_utc']>pretest_frozen
    assert decisions==sum(e['model_calls'] for e in eps)
    result=verify()
    result.update({'release_scope':'INTERIM_COMPLETION_SNAPSHOT','planned_episodes':690,
        'completed_episodes_in_release':663,'primary_analysis_episodes':660,
        'additional_completed_episodes':a['additional_completed_episodes'],
        'all_completed_model_calls':decisions,'snapshot_utc':a['snapshot_utc'],
        'snapshot_amendment_sha256':sha(HERE/'snapshot_amendment.json')})
    from verify_decision_alignment import verify as verify_alignment
    result['decision_alignment']=verify_alignment()
    verify_unchanged()
    write(HERE/'validation.json',result)
    print(json.dumps(result,indent=1))

if __name__=='__main__':main()
