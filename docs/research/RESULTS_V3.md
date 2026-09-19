# V3 Results

## Material Passport

- Artifact type: experiment result / living log
- Status: V3-0 COMPLETE; V3-1 ACTIVE
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

## Claim boundary

This is a readiness result, not evidence of continual learning, memory utility, reduced repair failures, or policy-value improvement.
