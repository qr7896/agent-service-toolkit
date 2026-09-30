# E1-C Blind Reproducer v4 preregistration and Fresh30 plan — 2026-09-25

## 1. Decision boundary

The previous blind reproducer path is not allowed to reopen C5 merely because a development diagnostic improves. C5 reopens only after an **independent, preregistered canary** shows at least one **treatment-only official resolved** task, zero baseline-only official resolved tasks, and no identity/safety/budget/infrastructure anomaly.

Fresh30 remains downstream of that gate. Until both the independent canary and same-version C5 n=30 gates pass, the Fresh30 task tree must remain unselected, unread, and unmaterialized.

## 2. Why v4 exists

The earlier paired C4 line had blind reproducer coverage of only **1/6**. Reproducer-v3 added broader generic probe extraction, but its final three untouched unresolved DEV rows failed zero-provider admission: **0/3 reproduced**, all available candidates passed, so the v3 live provider command was not run.

Those final three rows were then explicitly converted to **contaminated development rows**. Reproducer-v4 added issue-derived behavioral witnesses: reverse sliced-prefetch, migration operation-order, and inline issue-test/query assertion witnesses.

Zero-provider v4 diagnostic: django__django-15957, django__django-12754, and django__django-15280 all reproduced, for **3/3** coverage with **0 provider calls**. This is development-only evidence (`independent_canary_claim=false`), not efficacy evidence, and cannot open C5.

## 3. Independent-canary contamination rule

The current local E1-C task pool has already been used by historical solved runs, B4/C4, reproducer-v2/v3, or the v21-v50/public-evidence development line. Therefore no current local row may be relabeled as an independent v4 canary.

`evals/e1c_blind_repro_v4_selector.py` admits only an external three-task reserve with exact count 3, no overlap with the frozen contaminated identity set, metadata only (`instance_id`, `repo`, `base_commit`, `image`), no statement/test/gold/grader/outcome fields, `source=external_disjoint_canary_reserve`, and `identity_frozen_before_statement_materialization=true`.

Template: `data/e1c_blind_reproducer_v4_canary_manifest.template.json`. The real frozen identity file, once curated, is `data/e1c_blind_reproducer_v4_canary_manifest.json`.

The metadata-only freezer is `evals/e1c_blind_repro_v4_reserve.py`. It rejects task-content/outcome keys, excludes every contaminated identity, deterministically ranks eligible rows by `sha256(e1c-v4-independent-canary|instance_id)`, and writes exactly three identities together with the source revision. Candidates whose task text was exposed while investigating data access are added to the contamination denylist rather than reused.

Freeze order is mandatory: write and hash metadata-only identity first; only then materialize the three public task statements, exact base source trees, official images, and public admission artifacts.

## 4. Frozen v4 paired-canary protocol

Runner: `evals/e1c_blind_repro_v4_runner.py`. The runner reuses the already-reviewed v3 execution shell and changes the selector/reproducer mechanism. Baseline and treatment hold public issue/source/structural evidence constant; baseline withholds reproducer context, treatment receives the frozen v4 reproducer context. Candidate patches pass blind verification before official grading. No automatic retry.

Zero-provider sequence:

    .venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_repro_v4_runner preflight
    .venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_repro_v4_runner prepare
    .venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_repro_v4_runner live-preflight

The live provider command remains a separate explicit-authorization boundary:

    .venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_repro_v4_runner run-canary

Post-run gate:

    .venv\Scripts\python.exe -X utf8 -m evals.e1c_blind_repro_v4_runner c5-gate

C5 opens iff `treatment_only_resolved >= 1`, `baseline_only_resolved == 0`, `identity_anomalies == []`, and `expand_c5 == true`. Anything else is a preregistered stop.

## 5. C5 and Fresh30 v4

Fresh30 gate: `evals/e1c_fresh30_gate_v4.py`. Required order: independent v4 canary passes; same-version C5 n=30 runs; C5 must finish 30 attempted / 30 official resolved / completed; only then may a brand-new Fresh30 identity be selected and frozen before task-content inspection; then exact base source + official images are materialized; Base-Fail and independent Gold-Pass are required 30/30; finally a frozen one-shot measurement runs with no outcome-conditioned replacement.

Zero-provider planning command:

    .venv\Scripts\python.exe -X utf8 -m evals.e1c_fresh30_plan_v4 plan

Hard gate:

    .venv\Scripts\python.exe -X utf8 -m evals.e1c_fresh30_gate_v4 gate

Before the gate opens, `new_task_tree_touched=false` and materialization is forbidden.

## 6. Fresh30 measurement package

Primary: official resolved / 30. Secondary: blind reproducer coverage before provider call; model calls/tokens; files read/tool calls; abstentions; blind verification failures; official grader failures; infrastructure failures; forbidden source accesses; safety events. All frozen/admitted tasks remain in the denominator.

## 7. Current status

- reproducer-v4 development coverage: **3/3**, zero provider calls;
- independent v4 canary: **not yet curated/frozen**;
- v4 provider canary: **not run**;
- C5: **closed**;
- Fresh30: **closed**;
- Fresh30 new task tree: **untouched**.

Current infrastructure note: the Runner's Hugging Face lookup failed at DNS resolution (`getaddrinfo failed`) while attempting a metadata-only fetch. No task statement/test/gold content was materialized by that failed attempt. Reserve freezing therefore remains pending external metadata availability; the fail-closed C5/Fresh30 state is unchanged.

This is the furthest valid state before obtaining a truly disjoint canary reserve and explicitly authorizing the exact live provider command.
