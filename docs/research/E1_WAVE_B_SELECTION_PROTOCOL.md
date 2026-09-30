# Formal E1 Wave B Deterministic Curator Selection Protocol

Status: FROZEN_BEFORE_WAVE_A_OUTCOME
Frozen date: 2026-09-22
Scope: Formal E1 Wave B only
Target admitted cohort size: 18

## Purpose

This protocol freezes how the independent curator constructs Wave B before any Wave A outcome is inspected. It changes no Coding Agent algorithm, prompt, runtime, retrieval policy, tool policy, sandbox policy, grader, or analysis code.

## Candidate universe

Use public repository repair commits that can be checked out and executed in the isolated curator environment. The curator must not use Wave A outcomes, patches produced by the experimental editor, or any tuning-context signal when discovering, ordering, accepting, rejecting, or replacing candidates.

Candidate discovery must use the same public-source curation route used for the clean replacement cohort. Discovery stops only after 18 candidates have passed every eligibility check below. Discovery order must be recorded inside the sealed curator manifest.

## Eligibility filter

A candidate is admitted only if all conditions hold:

1. The base revision reproduces the targeted failure (Base-Fail).
2. The independently verified gold revision passes the targeted check (Gold-Pass).
3. The task is executable in the sealed harness without a provider/model call.
4. It is not a duplicate issue, patch lineage, or materially equivalent repair of another admitted Wave B task.
5. It has no duplicate issue/patch lineage with any Wave A task.
6. Its source commit does not overlap prior DEV/contaminated source commits or any Wave A source commit.
7. Required fixture, tests, gold patch, symbols, grader details, and task text remain sealed from the tuning/editor context.
8. The overlap/contamination audit passes.

A rejected candidate remains recorded in the sealed curator audit with a content-neutral rejection reason; rejected candidates are never counted in the 18-task denominator.

## Deterministic selection and replacement

The curator evaluates candidates in the recorded discovery order. The first 18 candidates that pass every eligibility condition are admitted. There is no outcome-based reordering, cherry-picking, balancing, or replacement.

If a candidate fails an eligibility check, continue to the next candidate in the pre-recorded discovery stream. If fewer than 18 eligible candidates are available from the initial repository set, expand discovery using the same public-source route and the same eligibility filter; record the expansion boundary and discovery order in the sealed manifest before evaluating the newly discovered candidates.

No bug/feature/refactor balancing target is introduced for Wave B. Adding an outcome-unrelated stratification after this freeze would create a new selection-protocol identity and must be disclosed before any Wave A outcome is used.

## Cross-wave independence

Wave B must exclude Wave A task lineage and Wave A source commits in addition to all previously excluded DEV/contaminated lineage. The independent curator may inspect the sealed Wave A provenance needed for this exclusion, but must not inspect or receive Wave A experimental outcomes.

## Handoff boundary

The tuning/editor context receives only content-neutral metadata allowed by the existing v10.7 admission schema: admitted task count, repository IDs, exact commit IDs, curation timestamps, overlap-audit result, source-commit-overlap flag, hidden manifest SHA-256, Base-Fail attestation, and independent Gold-Pass attestation.

Do not return task descriptions, issue bodies, source excerpts, tests, gold artifacts, expected values, task-specific identifiers, grader information, experimental outcomes, prompts/responses, or credentials.

## Fixed execution contract after curation

Wave B uses the already frozen Formal E1 intervention/control-plane identities. Planned ceiling: 18 provider calls and 39,600 total provider tokens, one call per task, 600 max output tokens, thinking off, no retry. Provider/model/infrastructure failures remain in the admitted denominator.

Wave A and Wave B are reported separately. A pooled descriptive resolved/30 may be added only after an explicit identity-compatibility check confirms the preregistered editor/runtime/model/intervention/analysis identities are compatible for pooling.

## Change control

This file is frozen before Wave A outcome inspection. Any later change to candidate discovery, eligibility, ordering, replacement, cross-wave exclusion, or handoff rules creates a new selection-protocol identity and must be disclosed. No such change may be justified using Wave A outcomes.
