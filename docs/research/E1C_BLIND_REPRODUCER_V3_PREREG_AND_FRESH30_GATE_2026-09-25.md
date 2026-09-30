# E1-C Blind Reproducer v3 — Preregistration and Fresh30 Gate

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan
- Origin Date: 2026-09-25
- Verification Status: CLOSED AT ZERO-PROVIDER ADMISSION GATE; V4 DEVELOPMENT CONTINUES
- Version Label: e1c-blind-reproducer-v3-prereg-v1

## 1. Why a new identity exists

The completed post-B4 C4 paired canary ended at baseline 0/6, treatment 0/6 and expand_c5=false. Its zero-call prep also showed that trustworthy blind reproducer coverage was the main bottleneck. A first reproducer-v2 development cohort still produced only 1/6 trustworthy reproducers.

Reproducer v3 is a mechanism change, not a retry of C4. On already contaminated development rows only, v3 adds: unfenced REPL transcript extraction, issue-derived setup completion, SymPy consistency witnesses, Django minimal model harnesses, exact original-test node targeting, repository-native test runners, infrastructure-failure rejection, and bounded audit probes. The zero-provider development diagnostic improved trustworthy reproducer coverage to 4/6. That 4/6 is development evidence only and is not a canary result.

## 2. Final canary cohort frozen before statement inspection

Selector: `evals/e1c_blind_repro_v3_selector.py`

Selector SHA256:

`9cdf52689055466d777245284628ad5afa59df8ff73ad03c135c49e9cd89050e`

The selector excludes historical solved rows, B4 rows, post-B4 C4 rows, and the reproducer-v2 six-row development cohort. Before reading the final statements, the remaining three unresolved DEV rows were frozen in manifest order:

- `django__django-15957`
- `django__django-12754`
- `django__django-15280`

All three are the complete remaining non-overlapping unresolved DEV set; no alternate row may be substituted after preparation outcomes are known.

## 3. Zero-provider admission gate

Runner: `evals/e1c_blind_repro_v3_runner.py`

Before any provider call:

1. exact source/image identity must pass;
2. all repair payloads must remain assertion-blind and pass boundary audit;
3. prep must complete for all three rows;
4. at least **2/3** rows must have `reproducer_status=reproduced_failure`;
5. infrastructure failures, timeouts, candidate passes and semantic mismatches do not count as reproduced failures.

If fewer than 2/3 have trustworthy reproducers, the final live paired canary is not run and C5 remains closed.

## 4. Paired canary protocol

Arms share the same issue statement, source commit, structured evidence, candidate paths, model, token budget, inspect budget, patch verification and official grader. The only treatment difference is that treatment receives the frozen reproducer context while baseline receives `withheld_from_baseline`.

Frozen budgets:

- tasks: 3
- arms: baseline + treatment
- max provider calls per arm: 2
- max output tokens per call: 900
- per-task-arm token ceiling: 9,000
- total token ceiling: 54,000
- retries: 0
- bounded inspect: at most one before final edit/abstain

Exact live command, requiring separate explicit authorization under repository policy:

`.venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_repro_v3_runner run-canary`

## 5. C5 gate

C5 reopens only if the final canary has:

- at least one treatment-only official resolved task;
- zero baseline-only official resolved tasks;
- no safety, leakage, budget or infrastructure anomaly that invalidates identity.

Otherwise `expand_c5=false` and the identity is sealed.

If C5 opens, the future same-version 30-DEV identity is:

`e1c-blind-reproducer-v3-c5-n30-v1`

It must be separately frozen and authorized. No result from historical best-of versions may be pooled into the same-version score.

## 6. Fresh30 gate

`evals/e1c_fresh30_gate_v3.py` must remain fail-closed until:

1. reproducer-v3 final canary passes its treatment-only gate;
2. one frozen same-version C5 run completes all 30 DEV tasks;
3. that exact run is 30/30 official resolved.

Only then may a new Fresh30 cohort be selected/admitted. Until that point the invariant is:

`new_task_tree_touched=false`

Fresh30 selection, task statement inspection, materialization and one-shot execution are prohibited before this gate opens.

## 7. 2026-09-25 Post-run result: v3 admission failed before any provider call

The frozen three-row v3 prep completed with provider_calls=0. All three rows were `no_reproducer / all_candidates_passed`. Live preflight therefore reported `reproduced_count=0`, `required_reproduced_count=2`, `coverage_gate=false`, `ready=false`. The exact v3 live command was not executed. Fresh30 v3 remains `ready=false` with `new_task_tree_touched=false`.

## 8. Reproducer v4 development result

After v3 preparation, those final three DEV rows are no longer independent and are development-only. Reproducer v4 adds issue-derived behavioral witnesses so that “code executes” is not confused with “issue behavior is correct”. The zero-provider diagnostic `e1c-blind-reproducer-v4-dev-diagnostic-v1` produced **3/3 reproduced_failure** using three distinct witnesses: reverse sliced-prefetch behavior, migration operation ordering, and inline issue assertions. The artifact is explicitly `development_contaminated=true` and `independent_canary_claim=false`; this does not reopen C5.

## 9. Independent canary and Fresh30 plan

The current 30-task DEV pool has no untouched unresolved rows left for another independent canary. The next legal sequence is: reserve a new disjoint canary pool before statement inspection; freeze a v4 paired selector/identity; require a zero-provider reproducer admission gate; run exactly one authorized paired canary; reopen C5 only for at least one treatment-only official resolved task with zero baseline-only resolved tasks and no safety/budget anomaly; then run one frozen same-version C5 n=30; only a true 30/30 official result may materialize Fresh30. Fresh30 remains one-shot, no retry, no historical best-of pooling, and must stay `new_task_tree_touched=false` until that gate opens.

