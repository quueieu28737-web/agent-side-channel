# R8 same-operation attribute scout

See DESIGN.md and protocol.json for the posthoc exploratory scope. Reuses original Sol episodes, with no LLM or new customer generation. The protocol freezes code and inputs before fitting; existing R4/R5/R7 files remain unchanged.

From a complete package checkout, with Python 3.12+:

```sh
python -m venv .venv
# Activate the venv using the command for your shell.
python -m pip install -r requirements.txt
python verify.py
```

All scripts resolve package sources relative to this directory. `prepare.py` independently reconstructs each full raw episode TLS record string and slices exact known-call boundaries. This is an oracle projection, not an automatic boundary detector. The saved records model TLS1.2 loopback replay; they are not captured provider traffic and have no measured timing.

To reproduce fitting, `python run.py` checks frozen code/input hashes before writing its outputs. `verify.py` separately checks source/label linkage, call projection, instance grouping, customer disjointness, exact model reload predictions, BA and 2000-draw customer bootstrap intervals. Models use Python pickle: load only the trusted local artifact whose hash is in verification.json.

Zero-vector operation-name and canonical constant-size controls are deliberately the same information-free feature representation. Finite pooled OOF BA can differ from 0.5 because fold-specific training priors/tie decisions interact with customer label composition; this is not information in a constant observation. No attack tuning or category search follows observed outcomes.

`python describe.py` recomputes the requested original-direction AUROC/fold addendum without fitting; `python make_table.py` prints proposed LaTeX. REPORT.md contains bounded main/supplement wording.
