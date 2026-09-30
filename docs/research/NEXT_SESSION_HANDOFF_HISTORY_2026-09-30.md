# Next Session Handoff — E1-B

Date: 2026-09-20

## Current state

The v10-v10.8 control plane is consolidated and frozen. Independent curation, real-metadata admission, exact config/preregistration and the five-artifact zero-call dry run are complete. Latest verified code baseline: **617 passed / 4 skipped / 33 warnings**. Current state is `READY_FOR_EXACT_COMMAND_AUTHORIZATION`; no replacement-held-out provider call has run.

Formal E1 Wave B pre-outcome governance is also frozen: `E1_WAVE_B_SELECTION_PROTOCOL.md`, SHA-256 `7bd230c46102a014da039c2981a36a01918ab5f47457e2be7b57e981987118f5`. A synthetic 18-task zero-call run verified that the existing control plane accepts the planned Wave B `18 calls / 39,600 tokens` package and materializes the exact five-artifact dry-run contract without provider calls.

Real pilot identity: run ID `e1b-8bbc8ba900559ce6`; package manifest `0f6846a989d3e0b2b17d0f9f90fcc9537ce31eb066a0e0bb8b109e14bd79f4d7`; freeze manifest `1494d741b0d3cb446f7669a94b54c2504fff1ffc6efe1644492ac990ebd1dc32`; admission manifest `43a949bdb733a55ea0dadaed7ec7dd8269fa1fca79768d70a32f57e12e1fbff6`; hidden cohort manifest `006b96c6a9b106a79a06885e51bf619df5e5afe1d649d38f7df4429c8cac2a12`.

## Read first

- `docs/research/E1B_V10_CONTROL_PLANE_AUDIT.md`
- `docs/research/E1_E2_FAST_COMPLETION_PLAN.md`
- `docs/research/E1_WAVE_B_SELECTION_PROTOCOL.md`
- `docs/research/WEBCODEX_HANDOFF_2026-09-20.md`
- `docs/research/E1B_REPLACEMENT_PILOT_PREREGISTRATION.md`
- `docs/research/E1B_EXPERIMENT_READINESS_CHECKLIST.md`
- `docs/research/E1B_RESEARCH_CONTRIBUTIONS.md`
- `docs/research/E1B_FUTURE_EXPERIMENT_MATRIX.md`
- `docs/research/RESEARCH_CLAIM_LEDGER.md`
- `docs/research/PENDING_E1B_AUTONOMOUS_TESTS.md`
- `docs/research/E1B_OFFLINE_DRY_RUN_OPERATOR_CHECKLIST.md`
- `docs/research/templates/e1b_replacement_cohort_metadata.template.json`
- `docs/research/templates/E1B_REPLACEMENT_COHORT_METADATA_README.md`
- `docs/research/templates/E1B_ONE_SHOT_PREREGISTRATION_TEMPLATE.md`
- `docs/research/templates/E1B_POST_RUN_REPORT_TEMPLATE.md`

## Frozen / may change

Treat v10-v10.8 semantics and experiment contracts as frozen. Change them only for a reproducible correctness/safety/reproducibility defect or a preregistered requirement existing contracts cannot represent. Documentation, external-cohort metadata plumbing that does not reveal task content, and analysis preregistration may continue offline.

## Forbidden without new exact authorization

Do not invoke any real provider/model, consume provider budget, rerun repeated DEV, execute/inspect the contaminated original six TEST tasks, inspect replacement held-out task content/outcomes, or inspect private SERBench/Test500. Generic “continue” is not authorization for a live command.

## Next tasks

1. In WebCodex, review documentation consistency, run `git diff --check`, and optionally rerun non-model focused/full regression. Do not inspect sealed content.
2. The desktop user may explicitly authorize the exact live command recorded in `WEBCODEX_HANDOFF_2026-09-20.md`.
3. If authorized, execute that command once on the desktop; do not retry or add budget.
4. Validate and analyze the five artifacts with the frozen analysis script, preserving all 12 tasks in the denominator.
5. Fill the post-run report with exact descriptive results and update the centralized log without broad efficacy claims.

After the 12-task pilot, follow the already frozen `E1_WAVE_B_SELECTION_PROTOCOL.md` without outcome-driven tuning: independently curate/admit the unconditional 18-task Wave B, freeze its package, run its zero-call admission/dry-run, then obtain separate exact live authorization and complete formal E1 at n=30 before starting E2.

## Authorization boundary

Stop immediately before the first command that would call a real model/provider or execute the one-shot held-out experiment. Present that exact command to the user and obtain explicit authorization for that command. Passing offline admission/package checks is not live authorization.
