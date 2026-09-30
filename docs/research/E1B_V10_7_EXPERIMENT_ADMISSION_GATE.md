# E1-B v10.7 Experiment Admission Gate

Date: 2026-09-20  
Schema: `e1b-experiment-admission-v1`

v10.7 is a fail-closed pre-experiment gate. It never starts, schedules, or authorizes a provider/model experiment.

Admission requires a verified v10.6 freeze manifest; content-neutral task-manifest metadata only; explicit data-isolation declarations; frozen model/editor/runtime/retrieval/tool/sandbox/analysis identifiers; positive provider call/token ceilings; one-shot frozen configuration; no source-commit overlap; Base-Fail and independently verified Gold-Pass attestations for replacement held-out material; and a clean runtime-feature leakage audit.

Pre-admission task metadata may expose task count, repository IDs, commit IDs, curation timestamps, overlap-audit result, manifest SHA256, and boolean Base-Fail/Gold-Pass attestations. It must not expose task/issue text, setup, hidden tests, gold source/patch, expected values, task-specific symbols, grader data, or outcomes.

The only decisions are `ADMIT_OFFLINE_READY` and `REJECT`. `ADMIT_OFFLINE_READY` means the offline protocol prerequisites are satisfied. It is not permission to make a provider call. Repository policy still requires the user to authorize the exact live command separately.

Claim boundary: admission readiness and protocol hygiene only; no repair-efficacy claim.
