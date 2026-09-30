# E1-C Strict Successor Reproducer Feasibility — 2026-09-26

## Scope
Zero-provider successor research after V25 SEALED NEGATIVE and the V23/V25 two-round ROI stop. Uses old DEV/non-canary evidence only. No V23/V25 canary content, task-specific paths, grader outcomes, Gold, or live model results are used to tune a successor.

## Old-DEV finding
V25 old DEV is already 6/6 consensus with minimum family support 2 and total family support 17. Three tasks have behavioral+semantic+structural consensus; the remaining old-DEV consensus is semantic+structural only. Therefore another family-count-only witness is not a justified successor objective.

A concrete old-DEV gap exists in the historical frozen witness chain: `django__django-11734` contains a projected issue Python scenario with a behavioral observable (`scenario_exit_code == 0`) and a production-localized candidate path, but the frozen witness is explicitly `execution_ready=false`. Later strict versions obtained semantic/structural consensus without proving that scenario executable. This is old DEV evidence, not V23/V25 canary evidence.

## Successor hypothesis
The next strict successor, if implemented, should add a generic fail-closed **scenario execution preflight**: only a previously safe typed Python-scenario witness may become execution-ready after a bounded sandboxed exact-base preflight proves that its imports/setup can execute without benchmark assertions, tests, Gold, task IDs, network, or repository-wide reads. A failed/unsupported preflight remains non-executable. Merely relabeling an existing `execution_ready=false` witness is prohibited.

## Predeclared development gate (before implementation/replay)
1. Provider/model calls = 0; old DEV/non-canary evidence only.
2. Preserve V25 old-DEV consensus coverage at 6/6 and minimum family support >=2.
3. Do not reduce V25 total family support below 17.
4. Increase the number of old-DEV tasks with a **genuinely execution-preflighted behavioral reproducer** above the current verified baseline, without treating textual behavioral claims alone as executed evidence.
5. Every promoted scenario must have a persisted preflight artifact containing exact-base/source identity, bounded command, network-disabled/sandbox policy, exit status, observable result, and hashes; unsupported setup fails closed.
6. Focused leakage/safety tests must prove no task ID, benchmark assertion, test patch, Gold, grader result, hidden test, or V23/V25 canary content enters the preflight.
7. Existing frozen/sealed V20–V25 artifacts remain byte-preserved; implementation uses a new strict-successor namespace. Historical non-strict `E1C_DEV_V26_FREEZE.md` is unrelated and must not be overwritten/relabelled.
8. Only if all gates pass may mechanism/prereg be frozen; only after that may a new metadata-only, non-overlapping independent canary identity be selected.

## Current blocker / decision
No generic scenario execution harness with the above fail-closed provenance has yet been validated in the current strict lineage. Consequently there is not yet evidence to freeze a successor or select a new canary. Creating a taxonomy-only V26 or flipping `execution_ready` would be metric inflation and is prohibited. Paid/live expansion remains paused.

## Next allowed action
Implement and test the generic zero-provider scenario-preflight mechanism against old DEV only, then run the predeclared gate. No new canary content, Docker image acquisition for a new canary, provider calls, C5, DEV30, or Fresh30 before that gate passes.

## Implementation progress
- Added `evals/e1c_strict_successor_scenario_preflight.py` as a new, unfrozen successor-development namespace. It does not execute or repair a witness; it converts a runner observation into an auditable promotion decision and fails closed unless the witness is safe typed `python_scenario`, observable is `scenario_exit_code == 0`, Docker command is network-disabled, exact-base identity matches, image identity is digest-pinned, execution did not time out, and return code is zero.
- Added focused fail-closed tests. Existing strict-v7 runner/IR plus successor tests: **14 passed in 0.29s** using project `.venv`.
- Static leakage audit found **0** occurrences of V25 canary identities, Gold/test patch names, or official F2P/P2P tokens in the successor preflight module.
- All six old-DEV official images are currently not cached. No Docker pull was started. Therefore no real old-DEV scenario has been promoted and the predeclared development gate is **NOT YET PASSED**.
- Exact-base source for old-DEV `django__django-11734` is locally materialized at `.codex/e1c/strict-v6/postfreeze-v1/django__django-11734/source`, Git HEAD `999891bd80b3d02dd916731a7a239e1036174885` with no reported dirty paths.
- An isolated local importability dry-run reached that exact source but failed closed at `ModuleNotFoundError: asgiref`. The project venv is therefore not a valid substitute for the official task execution environment. Dependencies were not installed ad hoc because that would create noncanonical execution provenance.
- Refined blocker: exact-base source is ready; a canonical old-DEV execution environment (preferably the official digest-pinned image) is not locally materialized.

## Gate hardening and current mechanical result
- Preflight artifacts now persist witness hash/path/observable, expected and observed exact-base commit, digest-pinned image identity, bounded command, network-disabled decision, exit/timing status, and stdout/stderr hashes. This closes the provenance gap in the original prototype without loosening promotion criteria.
- Added deterministic `evals/e1c_strict_successor_gate.py`. Combined successor + strict-v7 focused suite is **21/21 PASS**; Ruff and `py_compile` pass on all new successor files; combined static leakage audit has 0 forbidden hits.
- `data/e1c_strict_successor_development_gate_current.json` mechanically evaluates the predeclared gate using the frozen V25 old-DEV replay and zero real preflight promotions. Result: `gate_passed=false`. Every requirement passes except `execution_preflighted_behavioral_gain=false`. This is now the sole development-gate deficit.
- V25 frozen probe and V25 seal hashes remain unchanged during successor work.
- WebCodex infrastructure has duplicated both the canonical Docker pull and later full-pytest durable execution into paired jobs. These duplicates are treated as runner infrastructure artifacts, not independent experimental or validation repetitions; no additional manual retry is launched.


## Canonical environment acquisition result
- The only attempted old-DEV canonical environment, django-11734 digest `sha256:5ddbc111ccc7ed091855034eacff1c58347df158d6acd0c015feab17587d36a2`, did not commit. Two WebCodex duplicate infrastructure jobs both reached their original 1800s timeout. This is sealed as infrastructure-blocked, not an experimental result. No third pull or retry is authorized in this continuation.
- Blocker artifact: `data/e1c_strict_successor_env_acquisition_blocked.json` SHA-256 `2e90bd399341759e345ce20052e6c2b08fc156324f3833e1c9506b45f35f3117`.
- Current deterministic development gate remains **NOT PASSED**, with only `execution_preflighted_behavioral_gain` unmet. The successor remains unfrozen and no new canary may be selected.


## Candidate-space and regression closure
- Historical old-DEV replay artifacts contain exactly one unique typed executable-style witness: `django__django-11734` / `python_scenario`, witness SHA-256 `ac32193cfc9cf8ff2dbb203175e32f4341c22fd6e37ac0f8d6976ff5483d3cbd`. No `call_result` witness or alternate old-DEV typed target exists. Inventory: `data/e1c_strict_successor_old_dev_typed_witness_inventory.json` SHA-256 `44e65e189694f9b16dc374a9220e9ecfed4fe6b777716d331fe2e9ee58ea1f1a`.
- The previously failing Windows Streamlit cold-start test passed alone (1/1 in 0.76s) with no test or timeout changes.
- Canonical UTF-8 full non-model regression subsequently passed: **1016 passed, 4 skipped, 0 failed in 163.09s**. Thus full-regression readiness is clean; no assertion was weakened or skipped.
- The deterministic successor development gate remains false solely because `execution_preflighted_behavioral_gain=false`; canonical environment unavailability prevents the one compliant real old-DEV preflight. Successor remains unfrozen and no new canary may be selected.
