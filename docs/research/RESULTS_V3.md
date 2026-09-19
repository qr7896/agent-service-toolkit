# V3 Results

## Material Passport

- Artifact type: experiment result / living log
- Status: V3-0 through V3-6 COMPLETE; MECHANISM FROZEN
- Date: 2026-09-19
- Verification status: ANALYZED
- External model/API calls: 0
- Internal E1-B sealed TEST opened/called: 0/0

## V3-0 — Readiness audit

V3 began by auditing the existing trajectory-to-experience path rather than creating a second memory stack. The repository already contains a trajectory compiler, SQLite store, semantic/keyword retrieval, compatibility filtering, usage feedback, reversible isolation, and survival re-evaluation. These components are reusable.

The local inventory is not yet suitable for continual-policy evaluation:

| Item | Observed |
|---|---:|
| Trajectories | 8 |
| Succeeded | 2 |
| Review rejected | 3 |
| Read-only | 3 |
| Existing-compiler eligible | 5 |
| Trajectories with experience hits | 6 |
| Trajectories with original commit provenance | 0 |
| Persisted experiences | 1 |
| Persisted accepted/rejected | 1 / 0 |
| Schema-v2-complete persisted rows | 0 |

The readiness artifact is `evals/results/v3_experience_readiness.json`. It reports `inventory_valid=true` and `existing_compiler_reusable=true`, but schema v2, temporal provenance, positive/negative memory, and continual-evaluation gates are false.

## Decision

Start V3-1 with schema/provenance work. Do not train a learned prior and do not run a model experiment yet. The first required correction is to capture the repository commit at trajectory execution time; compiling later and reading the then-current HEAD is not valid temporal provenance.

## V3-1 — Started: execution-time provenance

New trajectories now declare `schema_version=v3-trajectory-v1` and carry `source_repo` plus `source_commit_at_execution`, captured before the planner runs. The existing compiler is reused and emits `schema_version=v3-experience-v2`, source repository, execution commit, and event time inside its extensible `extra` payload.

The compiler no longer falls back to the current HEAD when an old trajectory lacks execution-time commit provenance. Missing provenance stays empty, `applied` remains unknown, and survival re-evaluation fails closed. This prevents later compilation time from being mistaken for historical execution time. Existing databases are not overwritten or migrated in place.

Targeted startup regression: **14 passed / 0 failed / 4 dependency-deprecation warnings** across V3 readiness/schema and the existing Research Mode suite.

## V3-1 — Schema v2 completed

The compiler now records validation strength, lifecycle state/reason/time, and a deterministic compiler/config hash. The non-destructive JSON export path does not overwrite historical trajectory JSONL or the existing SQLite database, and missing historical commit provenance is not inferred from current HEAD.

## V3-2 — Chronological replay gate completed

The replay gate constructs a deterministic event-time stream with immutable trajectory ID as the ordering tie-break. Evidence eligibility is stricter than ordering: only trajectories with an event time strictly earlier than the current task can enter the past-memory window. Same-time rows cannot leak into each other. Same repository plus execution-commit aliases are blocked, and missing repository, execution commit, timezone, event time, or immutable ID fails closed.

## V3-3 — Deterministic reliability baseline started

A model-free reliability score and adoption/abstention decision now use lifecycle state, validation strength, observed help/harm usage, and survival/effectiveness signals. Invalidated memory scores zero and low-reliability memory abstains. This is a deterministic baseline only, not a learned prior or efficacy result.

Focused V3 schema/export/replay/reliability/conflict/ablation regression: **18 passed / 0 failed / 4 dependency-deprecation warnings**. V3-4 now adds deterministic event-age decay and conflict adjudication: opposite-outcome experiences with the same task signature are compared using reliability times decay; ties isolate both, otherwise the weaker experience is isolated. V3-5 has started with a matched four-arm offline artifact: no-memory, always-on, compatibility-only, and reliability-aware. All arms share the same strict past-only eligible pool; the reliability-aware arm fails closed when commit distance is unavailable. V3-3 now combines reliability, compatibility, and explicit commit distance in a deterministic adoption/abstention policy; unknown commit distance fails closed. The policy is integrated into strict chronological replay, so only past experiences are scored. V3-4 has started with explicit opposite-outcome conflict detection and reversible active↔isolated lifecycle transitions; existing survival/utility machinery remains reused rather than duplicated. External model/API calls remain 0 and the internal sealed TEST remains closed.

## Claim boundary

This is a readiness result, not evidence of continual learning, memory utility, reduced repair failures, or policy-value improvement.


## V3-5 — Matched ablation completed

The four-arm offline ablation now has a CLI/JSON artifact path and audit-only summary metrics for eligible-pool size, selected counts per arm, and reliability abstentions. These are mechanism/readiness metrics, not efficacy outcomes. A dry-run provenance audit on the existing non-sealed `.codex/trajectories/coding_agent.jsonl` found 8 rows but 0/8 with `source_repo` and 0/8 with `source_commit_at_execution`; therefore the chronological ablation correctly remains blocked rather than fabricating provenance or commit distance.

## V3-6 — Negative experience / counterfactual replay started

A model-free strict-past replay artifact now separates accepted and rejected historical experiences using the existing compiler outcome/failure_type fields. A sample becomes counterfactual-ready only when both positive and negative past evidence exist. This is readiness plumbing only; it does not infer that either historical action would causally change the current task outcome. Focused V3 regression: **20 passed / 0 failed / 4 dependency-deprecation warnings**. External model/API calls remain 0; sealed TEST remains closed.


## V3-6 — Completed and frozen

Counterfactual replay now reports both raw positive/negative availability and compatibility-matched positive/negative evidence, with an explicit claim boundary that evidence availability is not a causal counterfactual effect. The reliability audit found a temporal-leakage risk in untimestamped lifetime used/helped/harmful counters. Replay reliability now ignores those counters by default; they can influence reliability only when an explicitly past-visible snapshot opts in. A regression test proves later lifetime feedback cannot change the default earlier replay score.

The V3 mechanism is now frozen. `docs/research/V3_FREEZE_GATE.md` defines the minimum prospective trajectory schema and readiness gate. Existing non-sealed historical data remain blocked because execution-time provenance is absent. Focused V3 regression: **21 passed / 0 failed / 4 dependency-deprecation warnings**. Model/API calls: 0. Sealed TEST opened/called: 0/0.


## Prospective data gate instrumentation

The execution path was audited: `make_plan` resolves `trajectory_started_at`, `source_repo`, and `source_commit_at_execution` before awaiting the planner, then persists them into state; `build_trajectory` preserves the execution commit instead of recomputing it later. A prospective readiness validator/CLI now fails closed on missing provenance, invalid event timezone, malformed changed paths, missing retrieved-experience IDs, and untimestamped usage feedback. Focused frozen-V3 regression: **25 passed / 0 failed / 4 dependency-deprecation warnings**.


## Frozen pipeline collection smoke

Trajectory instrumentation now separates retrieved experience IDs from adopted experience IDs without changing the frozen adoption policy. Prospective readiness reports blocker distribution, provenance completeness, and chronological-replay minimum readiness. A synthetic non-sealed end-to-end smoke test validates readiness -> chronological replay -> four-arm matched ablation -> counterfactual readiness. This establishes pipeline connectivity only, not efficacy. Focused regression: **27 passed / 0 failed / 4 dependency-deprecation warnings**.


## Adoption observability audit

A follow-up audit found that `recall_experiences` records retrieval/compatibility hits but does not currently provide a definitive adoption event. The trajectory schema was corrected to avoid false precision: absent adoption observation is represented as `adoption_observed=false` with `adopted_experience_ids=null`, rather than an empty adopted set. Prospective readiness now exposes ready/blocked IDs in addition to blocker and provenance summaries. Focused frozen-V3 regression remains **27 passed / 0 failed / 4 warnings**.


## CLI finalization

Heavy experience-policy imports are now lazy for evaluation entry points. Root-level CLI help smoke for prospective readiness, chronological replay, memory ablation, and frozen pipeline completes in about 0.08 s per command in the current environment. Prospective readiness has a source-byte-preservation regression test. `v3-trajectory-v1` remains unchanged because the adoption observability fields are additive instrumentation under the frozen protocol. Focused regression: **29 passed / 0 failed / 4 warnings**.


## Prospective cohort execution preparation

The runtime write path was confirmed: normal Coding Agent completion appends the built record to the configured trajectory path, defaulting to `.codex/trajectories/coding_agent.jsonl`. A collection CLI now supports `preflight`, `start`, and `status`; status filters by the cohort start marker so the legacy eight-row history cannot be counted as prospective evidence. No new real prospective trajectories have been claimed in this preparation step. Collection-focused tests: **11 passed / 0 failed / 4 warnings**.


## Collection preflight hardening

Prospective preflight is now fail-closed: it performs read-only Git checks for repository root and HEAD commit, checks the trajectory parent with an OS writable check, and reports `ready_to_collect=false` when execution provenance cannot be established. Status also reports adoption-observation coverage for marker-scoped rows. `docs/research/V3_COLLECTION_RUNBOOK.md` is the operator sequence. No real prospective row has been created or claimed.


## Live preflight result

A real read-only preflight against `.codex/trajectories/coding_agent.jsonl` in the desktop checkout found the trajectory directory writable, readiness importable, and the Git root/HEAD available. It returned `execution_commit_available=true`, `ready_to_collect=true`, and `blockers=[]`. The cohort marker was intentionally not created yet because the frozen mechanism changes must first be committed and the non-sealed runner/model budget fixed. Focused V3 regression: **38 passed / 0 failed / 4 dependency warnings**. A broader V3 + legacy Research Mode run reached **47 passed** but one pre-existing `adaptive_retrieval_benchmark.py --help` import exceeded its 30-second test timeout; no V3 assertion failed. Model/API calls remain 0; sealed TEST opened/called remains 0/0.

The real-artifact path is not yet closed: `evals.v3_frozen_pipeline_smoke` always emits `synthetic=true`, so its output cannot pass the default real-only artifact audit. This is an explicit prospective-evaluation blocker; the marker must not be edited by hand and no efficacy claim is allowed until a provenance-checked real artifact entry point exists.
