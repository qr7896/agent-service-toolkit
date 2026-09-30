# E1-B Replacement Held-out Protocol

## Purpose

The original six nominal TEST fixtures were not executed, but their fixture content was exposed after the v3 DEV run. They are therefore excluded from clean confirmatory claims for v4 and later.

## Separation rule

A replacement held-out cohort must be curated outside the tuning context. Before the editor/runtime configuration is frozen, the tuning side may receive only cohort metadata needed to prove independence: task count, source-repository identifiers or commit hashes, creation timestamps, duplicate/overlap audit, and a cryptographic manifest hash. It must not receive issue text, setup-file content, hidden tests, gold patches, expected values, or task-specific symbols.

## Required cohort properties

- repository-level executable repair tasks with Base-Fail and independently verified Gold-Pass;
- no source-commit overlap with DEV or the contaminated six-task cohort;
- no duplicate issue/patch lineage across splits;
- hidden grader and gold artifacts inaccessible to the editor;
- task fixtures created or selected without using v4+ outcomes;
- frozen task manifest hash before the first confirmatory model call;
- one-shot execution under the frozen editor/model/evidence/tool/budget/sandbox configuration;
- full trajectory, calls, tokens, reads/writes, final patch hash, F2P/P2P and safety events retained.

## Quality audit before admission

Each task must be checked for prompt-test alignment, sufficient public specification, meaningful FAIL_TO_PASS coverage, regression coverage, and absence of implementation-detail-only grading. Ambiguous or broken tasks are rejected before any model outcome is observed. This follows the current coding-agent evaluation lesson that benchmark contamination and flawed tests can dominate measured capability.

## Freeze boundary

The replacement cohort may be generated/verified before v4+ freeze only by a separate curation process that does not reveal task fixtures to the tuning context. The tuning context receives the frozen manifest hash after curation. Once a candidate editor protocol is frozen, the held-out fixtures can be released only to the execution harness, not used for prompt tuning, and the complete cohort is run once.

## Reporting

Report exact counts rather than broad claims when n is small: resolved/tasks, F2P, P2P, calls/task, tokens/task, wall time, files read/written, safety violations, and failure taxonomy. DEV results and contaminated diagnostic results remain separate from replacement-held-out confirmatory results.
