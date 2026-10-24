# Complete portable dependencies

Use requirements-public.txt (dependency_versions_full.json), which adds the public sandbox pydantic dependency and pinned transitive packages to the initial analysis dependency record. This is an additive portability correction; the original analysis freeze record is retained unchanged.

From this experiment folder in a Python 3.12 virtual environment with the full public package structure:

```
python -m pip install -r requirements-public.txt
python -B verify_public.py
python -B verify_public.py --network
```

The revision-preview paths in analysis scripts are optional local dependency search paths; a portable installation uses the virtual environment packages when those paths do not exist. No Codex CLI, subscription credentials, API key or LLM request is needed.

For decision/event/prefix/tool/usage alignment using only public ZIP evidence, run python -B verify_public_decisions.py after verify_public.py. Then run python -B correct_verification_receipts.py to produce public_validation_corrected.json, which explicitly distinguishes known simulator-tool invocations from unknown-tool dispatch attempts. The original frozen-verifier receipt is preserved and linked by SHA; no raw model output is rewritten.

The public ZIP contains retained model evidence. Recomputing benchmark rewards and TLS analyses also requires the fixed checkout's pinned vendor/tasks/tools and helper source files; it is not a self-contained ZIP-only distribution. In corrected receipts and compact, real_tool_calls means known-name dispatch attempts (1003), including env.step errors, not successful executions. Original frozen summary/native receipts retain the legacy meaning total dispatch attempts (1015). Network call_ratio counts all test dispatch records, including unknown/errors/cover.

To independently recompute the separate 12-cell D2 all/writes-only/reads-only analysis from the public ZIP episode evidence and fixed checkout, run python -B verify_public_d2.py. public_d2_validation.json records exact suite BA/AUROC/CI/valid-draw and all per-model prediction equality, plus the analysis/verifier/dependency code hashes. It adds no LLM requests and does not modify frozen verify_public.py.

