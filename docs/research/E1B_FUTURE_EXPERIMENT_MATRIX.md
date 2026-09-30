# E1-B Future Experiment Matrix

Status: preregistration-facing design only. No held-out task content is inspected and no provider call is authorized by this document.

| Question | Arms | Independent variable | Primary outcomes | Cost/safety outcomes | Analysis boundary |
| --- | --- | --- | --- | --- | --- |
| Does adaptive acquisition outperform fixed retrieval? | frozen fixed lexical baseline; frozen deterministic adaptive stop/escalate; future learned policy only if separately frozen | acquisition policy | independently graded resolved/task outcome on clean replacement held-out | provider calls/tokens, retrieval actions, evidence volume, irrelevant-read proxy, safety/overreach violations | one-shot cohort; report all arms; no post-outcome prompt/policy tuning |
| Does structural escalation add value when lexical evidence is insufficient? | matched-budget lexical; matched-budget structural escalation | retrieval modality under matched initial state/budget | target/source coverage and downstream independent task outcome | retained evidence volume, cost/risk, tool calls | compare matched states/budgets; do not generalize modality superiority beyond cohort |
| Does experience memory help? | Memory OFF; frozen Memory ON | memory intervention | independent task outcome | input/output/total tokens, retrieval/tool calls, latency if preregistered | paired prospective tasks; report null/negative results; no cherry-picked successful trajectories |
| Does verification control reduce unsafe/unsupported execution? | verifier/control OFF baseline if ethically/safely runnable; frozen control ON | control-plane enforcement | task outcome plus blocked-invalid-action count | overreach/safety violations, unnecessary reads/actions, false-block rate | safety metrics co-primary; do not equate more blocking with better repair |

## Fixed metadata-level rules

Before any confirmatory run: freeze task-manifest hash, exact source commits, model/version, editor prompt hash, runtime/retrieval/tool/sandbox/analysis hashes, provider ceilings and analysis script. Require no DEV/contaminated-six source-commit overlap, Base-Fail attestation and independently verified Gold-Pass attestation.

Primary confirmatory results must be reported for the complete admitted cohort. Missing/failed provider calls remain visible in the ledger rather than being silently retried or dropped. Any retry policy must be frozen before the run. No task-specific prompt adjustment or policy update is allowed after held-out outcomes become visible.

The current local deterministic/oracle results may motivate hypotheses but are not substitutes for clean autonomous held-out evidence.
