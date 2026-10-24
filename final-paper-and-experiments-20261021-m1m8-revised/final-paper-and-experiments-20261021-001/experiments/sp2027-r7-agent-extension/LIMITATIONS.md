# Scope and limits

- This is a same-provider second-model evaluation using gpt-6-luna/low through the authenticated Codex subscription CLI app-server; no API key is used.
- The structured-action harness executes real pinned retail sandbox tools. It is not a native function-calling API evaluation. Planner and simulated user both use Luna, in separate fresh contexts.
- The immutable provider weight snapshot, temperature and provider random seed are unavailable. Episode seed=0 is an inherited repetition namespace, not a provider seed.
- Public tasks and customers were previously exposed in manuscript development. The 150-run cohort has 75 task IDs, 34 distinct existing customers, two prompts and one repetition. It does not add 150 customers or 150 distinct tasks.
- Customer groups are disjoint between inherited training and test partitions. Formal train has 29 tasks/10 customers; test has 46 tasks/24 customers, with five cancellation-positive and seven return-positive customer clusters.
- The selected training cohort is smaller than the existing Sol training cohort. Differences between Sol and Luna do not identify a causal model effect. D2 results are descriptive, with few positive customer clusters.
- The 10-run feasibility pilot is excluded from the formal 150 and has a documented protocol wording deviation. No old data, old protocol or old manifest was changed.
- Inference calls are not retried automatically in formal collection. Every failure is recorded, each call has a 180-second model-turn bound, and three consecutive failed episodes without a new result stop scheduling. Already active calls may finish. No account rotation or quota bypass is used.
- There is no live-cover replanning experiment and no independent human audit in this extension.
