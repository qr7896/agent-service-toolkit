# V3 Results

## Material Passport

- Artifact type: experiment result / living log
- Status: V3-0 through V3-6 COMPLETE; MECHANISM FROZEN
- Date: 2026-09-20
- Verification status: ANALYZED
- External model/API calls: 12 V3 calls / 17,777 provider tokens in total; only finalized artifacts are interpreted below
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

## Compact prospective cohort and first matched pair

The compact non-sealed cohort now contains four provenance-complete trajectories. The first three tasks passed their hidden graders using 2,379 provider tokens. A fourth real commit-replay task used one `deepseek-flash` call and 907 tokens but failed its hidden grader: the patch rebuilt an incomplete workspace, yet also deleted complete existing workspaces instead of preserving them. The failure was retained and not retried. The cohort therefore has three successes and one failure using 3,286 provider tokens; this small, selected pilot is not reported as an Autonomous Repair Rate.

Collection status reports 4/4 replay-ready rows, zero blocked rows, and provenance completeness 1.0. The real frozen evaluation is `ready=true`, `synthetic=false`, and passes the artifact audit. At the frozen default reliability threshold 0.6, selected experience count remains zero. The new failed trajectory supplies negative experience for future strict-past tasks but does not itself create another eligible pair at threshold 0.375.

The first exploratory matched memory pair remains n=1: memory OFF and ON both passed with the same patch hash; ON consumed 1,165 tokens versus 1,032 OFF (+133, +12.9%). It is classified as `redundant_memory`. This is descriptive only and does not show that memory helps, harms, or is generally useless. Full non-model regression after the update: **446 passed / 4 skipped / 33 warnings**. Internal E1-B sealed TEST opened/called remains 0/0.

## Non-sealed pilot runner readiness

The three-task chronological commit-replay pilot now has persistent workspaces/checkpoints, a fail-closed provider-token ledger, the canonical `deepseek-flash` model ID, thinking disabled, a 30,000-token global ceiling, 10,000-token task admission reserve, four-call task ceiling, 600-token output ceiling, and hidden external graders. Task preflight is **3/3 Base-Fail + Gold-Pass**. Focused budget/runner and related V3 tests passed; the broad suite reached **427 passed / 4 skipped**, with two unrelated environment/timing failures (Streamlit home resolution and a pre-existing 30-second CLI timeout). At this readiness checkpoint, no cohort marker or prospective row existed, model/API calls were 0, and sealed TEST opened/called was 0/0.

## Non-sealed pilot execution stopped at budget gate

Collection `v3-prospective-001` started on clean commit `946c718`. Task 1 completed three `deepseek-flash` calls and consumed **10,814 provider tokens** (10,180 input / 634 output), exceeding its fixed 10,000-token ceiling before producing a patch. Tasks 2–3 were not started. The failure exposed unbounded tool-result context and provider-billed tool schemas missing from the message-only reserve estimate. Tool results are now bounded and tool-bound calls reserve an additional 3,500 tokens; these hardening changes do not retroactively convert the run into a successful task. Prospective finalized trajectories remain 0, sealed TEST opened/called remains 0/0, and no repair-rate or memory-efficacy claim is made.

## Fifth compact trajectory and second matched pair

A fifth non-sealed commit-replay task extended the compact cohort without changing the frozen V3 mechanism. Its offline gate passed Base-Fail + Gold-Pass and its 1,928-token admission reserve was below the 4,000-token task ceiling. The single authorized `deepseek-flash` call used 442 tokens and returned an empty edit list; the hidden grader therefore remained failing. The failure was retained without retry. The compact cohort is now five provenance-complete, replay-ready rows: three successes and two failures using 3,728 provider tokens. This selected pilot is not an Autonomous Repair Rate.

The new row created one strict-past eligible pair at exploratory threshold 0.375. In the matched run, memory OFF used 460 tokens and memory ON used 578 tokens; both returned empty edits, failed the same grader, and had the same empty patch hash. The ON arm did receive and record adoption of the eligible past experience, but success delta was zero and token delta was +118. This pair is classified as `redundant_memory`.

Across the two exploratory pairs, one pair passed in both arms and one failed in both arms. Both had identical OFF/ON patch hashes and zero success delta; ON added 133 and 118 tokens respectively. The aggregate remains descriptive n=2 evidence only: it supports neither a beneficial nor a harmful memory-efficacy claim. Full non-model regression is **447 passed / 4 skipped / 33 warnings**. V3 cumulative provider usage is 12 calls / 17,777 tokens: normal pilot 3/10,814, compact cohort 5/3,728, and paired experiments 4/3,235. Internal E1-B sealed TEST opened/called remains 0/0.
