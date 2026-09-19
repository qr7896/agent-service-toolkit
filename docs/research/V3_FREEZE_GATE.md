# V3 Freeze Gate

## Status

Mechanism development is frozen after V3-6 unless a validation failure requires correction.

## Minimum prospective trajectory fields

- immutable trajectory ID
- timezone-aware event time
- source repository
- source commit captured at execution
- task text and changed paths
- execution outcome and structured failure type
- test/review evidence when observed
- retrieved and adopted experience IDs as distinct events
- timestamped usage/help/harm feedback if usage feedback is used by replay

## Readiness gate

Prospective evaluation may start only when chronological replay can be built without inferred provenance, commit distance is available or explicitly abstained, and each compared arm sees the same past-only eligible pool.

Historical lifetime usage counters without event timestamps are excluded from replay reliability by default. They may be used only from an explicitly reconstructed past-visible snapshot.

## Minimal prospective plan

Collect new non-sealed trajectories under the frozen schema before any model-policy claim. First report provenance completeness, positive/negative experience availability, matched replay coverage, abstention rate, and independent task outcomes. Do not open sealed TEST or tune on it.


## Instrumentation status

`make_plan` captures repository identity and execution commit before awaiting the planner, and `build_trajectory` preserves those state values. `evals/v3_prospective_readiness.py` now provides a fail-closed JSON readiness artifact for new non-sealed collections. Existing historical rows remain blocked rather than backfilled.


## Collection pipeline

New trajectories now persist retrieved experience IDs separately from `adopted_experience_ids`. The readiness artifact reports blocker counts, provenance completeness, and whether at least two valid rows exist for chronological replay. A synthetic non-sealed smoke test connects readiness -> replay -> frozen four-arm ablation -> counterfactual readiness without model/API calls.


## Adoption observability correction

The retrieval layer currently produces compatible experience hits but does not emit a definitive adoption event. Therefore new trajectories use `adoption_observed=false` and `adopted_experience_ids=null` unless an explicit `adopted` field is present. An empty list is reserved for an observed adoption decision where no experience was adopted; it is not used to imply observation.


## CLI and additive-schema finalization

Evaluation CLIs now defer heavy experience imports until policy/counterfactual computation, so root-level `python -m evals... --help` remains lightweight. The trajectory schema identifier remains `v3-trajectory-v1`: `adoption_observed` and related manifest fields are additive instrumentation under the frozen protocol, not a semantic policy/schema break. Prospective readiness is non-destructive and has a byte-preservation regression test.


## Prospective cohort execution gate

Normal Coding Agent completion calls `append_trajectory(record, trajectory_path(config))`, whose default target is `.codex/trajectories/coding_agent.jsonl`. `evals/v3_collection.py` now creates a non-sealed collection marker without fabricating a trajectory, performs a collection preflight, and reports only rows whose `ended_at` is on or after the marker start time. Historical rows before the marker are excluded. No real prospective row is claimed until the Coding Agent actually produces one.


## Collection preflight hardening

Prospective preflight is now fail-closed: it performs read-only Git checks for repository root and HEAD commit, checks the trajectory parent with an OS writable check, and reports `ready_to_collect=false` when execution provenance cannot be established. Status also reports adoption-observation coverage for marker-scoped rows. `docs/research/V3_COLLECTION_RUNBOOK.md` is the operator sequence. No real prospective row has been created or claimed.


## Live preflight result

A real read-only preflight against `.codex/trajectories/coding_agent.jsonl` found the trajectory directory writable and readiness importable, but this WebCodex execution environment exposes no Git repository root/HEAD. Therefore `execution_commit_available=false` and `ready_to_collect=false`; no cohort marker was created. Collection start is now gated by a preflight artifact and records its provenance snapshot.
