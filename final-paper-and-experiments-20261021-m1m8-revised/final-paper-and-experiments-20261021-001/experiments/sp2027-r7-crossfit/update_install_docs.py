from pathlib import Path
import re
h=Path(__file__).resolve().parent
for d in [h,h.parent/'sp2027-r7-localization']:
 p=d/'README.md';s=p.read_text(encoding='utf-8-sig');name=d.name
 block=f'''From the package root (the directory containing `experiments/`), create an isolated Python 3.12 environment and install this experiment's actual pinned dependencies. The public PyTorch CPU index is included in `requirements.txt`.

```powershell
py -3.12 -m venv .venv-r7-cv
.venv-r7-cv/Scripts/python.exe -m pip install -r experiments/{name}/requirements.txt
.venv-r7-cv/Scripts/python.exe -B experiments/{name}/verify.py
```

On POSIX, use `python3.12 -m venv .venv-r7-cv` and `.venv-r7-cv/bin/python` for the two Python commands. These requirements pin NumPy 2.5.4, SciPy 1.18.1, scikit-learn **1.9.0**, joblib 1.6.0, and torch 2.14.1+cpu. Do not substitute the agent-extension/Luna requirements, which use scikit-learn 1.9.1. The ignored `revision-preview/r7-deps` and `revision-preview/r3/deps` paths used during development are optional local setup details, not prerequisites for readers.'''
 s=re.sub(r'From (?:the )?repository root.*?```.*?```',lambda m:block,s,count=1,flags=re.S)
 s=s.replace('28 existing source/data files','36 existing source/data files').replace('these 28 package-relative dependencies','these 36 package-relative dependencies').replace('only 28 existing','only 36 existing').replace('only28','only36')
 s+='\n\nThe closure now also explicitly includes the eight R4 split/protocol/runtime and inference-fingerprint inputs discovered during relocated execution. The five snapshot fingerprint files are checked against the original runtime manifest’s `sp2027-r4` keys under a single fixed snapshot alias; split/protocol use the original scalar SHA fields, and runtime SHA remains bound to a hash-verified original episode. There are 36 dependency entries, including source and non-Python inputs; the runtime manifest is also one of three authority anchors.\n'
 p.write_text(s,encoding='utf8')
