import os, sys, json, hashlib, zipfile, datetime
from pathlib import Path
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'): os.environ[k]='1'
HERE=Path(__file__).resolve().parent
R6=HERE.parent/'sp2027-r6-timing'
sys.path.insert(0,str(R6))
import analyze as r6
from r6common import lib
from features import features
import numpy as np
SEED=20261025
MEASURED=['raw','padding','shadow_serial','shadow_parallel2','tunnel_2ms','tunnel_5ms']
SIMULATED=['bucket1024','tamaraw','tamaraw_fast','front','wtfpad','walkie_talkie','front_shift']
CONDITIONS=MEASURED+SIMULATED
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x): Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def key(r):return f"{r['prompt']}-t{r['task']:03d}-r{r['repeat']}"
def seed(r,cond):return int(hashlib.sha256((key(r)+'|'+cond).encode()).hexdigest()[:8],16)
def captures(part): return r6.captures(part)
def source_hashes():return {p.name:sha(p) for p in sorted(HERE.glob('*.py')) if p.name not in ('report.py','verify.py','power.py')}
def save_rows(path,rows):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for r in rows:z.writestr(key(r)+'-'+r['condition']+'.json',json.dumps(r,separators=(',',':')))
def rows(part):
    with zipfile.ZipFile(HERE/(part+'.zip')) as z:return [json.loads(z.read(n)) for n in z.namelist()]
