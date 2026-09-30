# V3 Generic Runtime Freeze — 2026-09-23

Status: **FROZEN_FOR_FRESH_COHORT_VALIDATION**

This supersedes the earlier candidate freeze for future clean-cohort claims. The compact-004/005/006 development tasks remain development evidence only.

## Genericization completed before fresh-cohort outcomes

Failure-class escalation cards no longer encode task-specific hidden contracts learned from compact development graders. They now use only the task statement, supplied bounded source excerpts, and runtime-visible guard output. Missing-symbol, interface, and preservation escalation therefore carry generic repair instructions rather than development-task answers.

The pilot grader runner now catches `subprocess.TimeoutExpired`, emits exit code 124 plus `timed_out`, and distinguishes whether tests had started. This supports candidate-timeout versus grader-bootstrap-timeout attribution without dropping the task.

## Frozen runtime controls

- bounded source excerpts
- structured exact edits
- executable verification guard
- generic failure classification and selective escalation
- maximum two compact provider calls per task
- 4,000-token compact task ceiling
- localized escalation reserve multiplier 1.0 and max output 400
- deterministic patch application and re-grade
- no outcome-driven prompt/policy/evidence-range/budget tuning on E1-C

## Validation evidence at freeze

Focused regression: 20 passed, 0 failed. Ruff on E1-C curator/runtime/pilot tests: all checks passed.

## External execution boundary

E1-C live remains dependent on a container-capable execution environment. The current WebCodex Windows runner has neither Docker nor WSL installed; this is an infrastructure prerequisite, not a runtime-policy change.
