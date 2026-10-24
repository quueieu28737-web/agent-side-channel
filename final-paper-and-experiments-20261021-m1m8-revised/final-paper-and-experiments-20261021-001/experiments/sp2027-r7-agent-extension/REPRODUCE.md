# Portable recomputation

Use Python 3.12 with numpy, scikit-learn, scipy, joblib, threadpoolctl, cloudpickle, and cryptography. Exact versions are recorded in dependency_versions.json. Keep the public package structure because pinned public retail tools and inherited attacker helpers are read from sibling directories. No Codex login or model requests are needed for recomputation.

From the experiment directory, after installing those versions in your own environment:

```
python verify_public.py
python verify_public.py --network
```

The first command validates the public ZIP file hashes, reconstructs all 150 formal episodes from that ZIP, checks requested/reported model identifiers, checks the frozen collection sources, and replays real tools to recompute native rewards. It does not read the original raw connectivity/pilot/formal directories. The second command additionally repeats training-only calibration on 58 training trajectories and local TLS replay/attacker evaluation on all 150 trajectories, checking all reported network suite metrics against the saved report. No LLM requests are made.

Public ZIP serialization and user-home path substitutions are fully documented in PUBLIC_REDACTION.json; raw scientific outputs are retained locally. The new D2/network analyses were appended during formal collection before any test output was available. They are not part of the original collection freeze; APPENDED_ANALYSIS_FREEZE.json records their own timestamp and hashes. Formal_plan.json is unchanged.

Calibration uses 29 tasks x 2 prompts = 58 training trajectories from 10 existing customers. Evaluation uses 46 tasks x 2 prompts = 92 test trajectories from 24 disjoint existing customers. The TLS link is the local agent-tool replay link; neither model-provider transport nor live agent replanning is measured.
