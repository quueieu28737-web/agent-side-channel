# Second-model operation-signature replication

## Frozen scope

The endpoint requests and returns `MiniMax-M3`. The experiment owner reports
that this deployment uses `deepseek-v4-flash`; no immutable model revision or
independently authenticated backend identity has been supplied. Preserve both
facts when reporting this experiment.

This extension uses the original 115 retail tasks and customer-disjoint
69/46-task training/test split (29/24 customers). Each task has one episode
under the standard prompt and forced native `tool_use` structured actions.
Both planner and simulated user use separate
contexts on the supplied endpoint. This is an additional model/deployment
sample on known tasks, not a fresh-customer confirmation.

`run.py` collects training episodes, freezes the training-only joint defense,
then collects test episodes and captures 230 local TLS sessions for undefended
and joint-program conditions. These replay the actual model trajectories;
they do not rerun the planner under live cover. Logical reward inheritance
and network intervention are separate measurements.

`finish_analysis.py` waits for this stage, then runs the frozen network
comparison, dispatch ablation, ciphertext write-exchange localization and
offline checks. Test outcomes never calibrate the cover templates or caps.
The localization selects exchanges using true tool names, then evaluates only
their TLS record lengths, directions and order. Its fixed inherited learners
are distinct from the expanded Sol cross-fit union.

## Credentials and execution

`launch.ps1` loads an encrypted Windows current-user DPAPI credential from
`LOCALAPPDATA/AgentSideChannelResearch`, outside the repository, and injects it
only into the child process environment. API keys, headers and private model
reasoning are never serialized by the adapter. Preserve TLS verification.
Do not start a second collector while one is active.

`interface-preflight-v1` preserves the entire initial text-JSON interface
attempt (eight completed episodes plus any unfinished requests). A task-free
capability probe confirmed native structured output support. All 115 formal
tasks are therefore collected afresh under the newly frozen native interface;
none of these preflight episodes enters formal inference or outcome analysis.
`INTERFACE_AMENDMENT.json` records this interface change and prior-file hashes.

Completed formal episodes and individual model responses are cached. Infrastructure
errors stop the collector; normal model protocol errors remain unsuccessful
episodes. The first parser implementation incorrectly classified a non-JSON
response as an infrastructure error. `PARSER_AMENDMENT.json` documents the
correction and cache fingerprint migration within that preflight, and
`parser-v1-evidence.zip` preserves the pre-correction records. Every preflight
decision remains archived separately from the new formal cohort.

## Publication gate

Publish only after all 115 episodes, replay and verification complete. Keep
existing Sol and Luna results intact. Promote the Luna replication alongside
the new model results, with their different training sizes, prompt counts,
attacker suites and calibration chronology explicit. Update manuscript,
supplement and package receipts together; unfinished collection is not a
completed experimental result.
