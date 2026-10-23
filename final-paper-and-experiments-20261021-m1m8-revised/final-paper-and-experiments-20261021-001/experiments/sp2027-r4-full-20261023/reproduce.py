"""Rebuild the complete cohort offline from the immutable base plus this delta.

Default: execute the original frozen full-cohort verifier. --reanalyze also
refits the fixed attacker suite and checks exact equality with saved results.
No model requests. Reconstruction occurs in an isolated temporary directory.
"""
from pathlib import Path
import json, shutil, sys, tempfile, zipfile
from verify_extension import HERE, EXP, BASE, read, sha, archives, episode_paths

def main():
    a=read(HERE/'inputs.json')
    for n,d in a['base_files'].items():assert sha(BASE/n)==d,n
    for n,d in a['inputs'].items():assert sha(HERE/n)==d,n
    with tempfile.TemporaryDirectory(prefix='agent-r4-full-') as td:
        work=Path(td)
        for dst,src in a['source_files'].items():shutil.copyfile(BASE/src,work/dst)
        for n,p in episode_paths().items():
            assert sha(p)==a['all_episode_hashes'][n]
            dst=work/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
        for n in ('sessions.json','predictions.json','results.json'):shutil.copyfile(HERE/n,work/n)
        # The original verifier reads requests from these archives. Outputs and
        # attempts remain in the original archives and verify_extension checks
        # their complete alignment separately, without duplicating the release.
        for arm in ('baseline','rules'):
            with zipfile.ZipFile(work/('model-records-'+arm+'.zip'),'w',zipfile.ZIP_STORED) as dst:
                for p in archives():
                    with zipfile.ZipFile(p) as z:
                        for n in z.namelist():
                            if n.startswith('runs/'+arm+'/') and n.endswith('/request.json'):dst.writestr(n,z.read(n))
        for folder in (EXP/'reviewer-audit',EXP/'sp2027-r2',EXP/'sp2027-r2/agent',EXP/'sp2027-r3'):sys.path.insert(0,str(folder))
        sys.path.insert(0,str(work))
        import common
        common.EXP=EXP
        original=common.sha;cache={}
        def cached(path):
            path=Path(path).absolute()
            if path not in cache:cache[path]=original(path)
            return cache[path]
        common.sha=cached
        if '--reanalyze' in sys.argv:
            import evaluate
            evaluate.main()
            for n in ('results.json','predictions.json'):assert read(work/n)==read(HERE/n),n
            print('ATTACKER_REFIT_AND_RESULTS_EQUAL',flush=True)
        from verify_r4 import verify
        result=verify()
        assert result==read(HERE/'validation.json')
        for p,d in cache.items():assert original(p)==d,('Input changed',str(p))
        print(json.dumps({'status':'FROZEN_FULL_VERIFIER_REPRODUCED','validation':result},indent=2))

if __name__=='__main__':main()
