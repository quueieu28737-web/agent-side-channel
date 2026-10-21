# E8: autonomous-agent experiment (checklist item B3)

This directory contains the complete pipeline for running tool-calling LLM agents on the
115 τ-bench retail tasks and evaluating cover and framing against the same attackers as
E6 and E7. **No LLM result is included.** No model API key was available during this
revision. The committed runs in `runs/` use stand-in planners and only validate the
pipeline.

| Step | Command | Notes |
|---|---|---|
| 0. Backend check | `python -B test_backends_mock.py` | Runs the OpenAI-compatible and Anthropic code paths against a local mock server. Checks tool-call parsing, caching and `--cache-only` replay. |
| 1. Trajectories | `python -B run_agent_episodes.py --agent openai --agent-model <m> --user openai --user-model <m> --out runs/<m>` | Resumable. `--max-tokens` sets a hard budget. Every request/response pair is cached in `runs/<m>/llm_cache/`. |
| 2. Cover + TLS + eval | `python -B apply_cover.py runs/<m>` | Applies online cover, replays the TLS sessions (about 10 min) and runs `../e67_eval.py`. |
| 3. Tables | `python -B make_e8_table.py` | Add the new run to the `runs` list first. |

## Design decisions
* **One trajectory serves every policy.** Sandboxed cover never reaches the agent and
  framing does not change content, so the agent's behaviour cannot depend on the defense.
  This cuts model cost 8× compared with E6's design. Live cover would change what the
  agent observes, so it is excluded; it needs a separate run for each policy.
* **Online cover.** Before each real call the dispatcher decides using only the history,
  and it flushes any remaining cover at the end of the session. The result is reported
  next to the offline (plan-aware) E6/E7 numbers.
* **Native reward** is recomputed exactly as in `tau_bench/envs/base.py`: database hash plus
  required output strings. The scripted run scores 1.0 on all 345 episodes, which checks
  the implementation. DB, account and object equality are kept as separate fields.
* **Labels.** The secret is the user's task intent (whether the reference program contains a
  cancellation or return). The agent's actual attempts are recorded separately.

## Budget for the LLM run
Each episode uses about 8–15 agent turns and 3–6 user turns, with about 6k tokens of
context per turn (policy plus tool schemas). That is roughly 115 × 3 × 15 × 6k ≈ 31M input
tokens for one agent model, plus the user simulator. Start with `--seeds 1 --tasks 0,...,29`
as a pilot. Report the model version, date, temperature and the `llm_cache/` hash in the paper.

## Stand-in results (`runs/`, synthetic)
`scripted` replays the reference programs. `noisy-scripted` inserts extra reads with
probability 0.3 before each reference call. Online shape equalization with constant
framing gives a balanced accuracy of 57.5% [50, 65] for cancellation (scripted) and 60.5%
[52, 70] (noisy), compared with 54.4% offline. The noisy planner overflows the template in
20.9% of sessions. See Supplement S13.
