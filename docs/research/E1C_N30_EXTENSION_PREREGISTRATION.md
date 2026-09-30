# E1-C N=30 Runtime Validation Extension

Status: **FROZEN_BEFORE_E1C_OUTCOMES**
Date: 2026-09-23

## Purpose

E1-C is a new post-hardening operational validation cohort. It does not modify, replace, or pool into the completed Formal E1 n=30 result. Its purpose is to test the frozen post-hardening runtime on 30 new tasks before committing to Formal E2.

## Cohort

- target: 30 newly admitted tasks
- exclude all Formal E1 Wave A/Wave B lineage and source commits
- exclude compact pilot tasks 01–06 and any development/tuning lineage
- discovery: public Python repair tasks, using SWE-bench/SWE-bench Verified, BugsInPy, or reproducible public GitHub repair commits
- deterministic admission: recorded discovery order; first 30 candidates passing every eligibility condition
- eligibility: Base-Fail, independent Gold-Pass, executable harness, no duplicate issue/patch lineage, no excluded source-commit overlap, contamination audit pass
- task/test/gold/grader content remains outside the tuning context

## Frozen intervention

Use the runtime frozen in `V3_RUNTIME_FREEZE_2026-09-22.md` unchanged:

- bounded source evidence
- structured exact edits
- executable guard
- failure classification and class-specific selective escalation
- maximum two provider calls per task
- 4,000 provider tokens per task ceiling
- escalation reserve multiplier 1.0; escalation max output 400
- no outcome-driven prompt, evidence-card, range, budget, or policy tuning

E1-C ceiling: 30 tasks × 4,000 = 120,000 provider tokens; maximum 60 provider calls. No automatic third call and no retry after the frozen two-stage policy is exhausted.

## Outcomes

Report exact denominator 30. Primary operational outcomes: final resolved, first-pass resolved, selective-salvage count/rate, provider infrastructure failure, verification failure, calls/task, tokens/task, total tokens, forbidden access, and safety events.

## Gate to E2

E1-C is diagnostic and cannot repair the old Formal E1 result. For the E2 operational gate, require artifact completeness 100%, critical safety violations 0, and provider/infrastructure failure rate <=10% (<=3/30). Report efficacy descriptively; do not create a success threshold after observing outcomes.

## Change control

After the first admitted E1-C outcome is visible, runtime/prompt/policy changes terminate this identity. Reproducible infrastructure-only fixes require a disclosed new execution identity; prior rows remain in the denominator and are not silently rerun.
