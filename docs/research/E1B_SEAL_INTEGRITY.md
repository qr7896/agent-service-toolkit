# E1-B Seal Integrity Log

## 2026-09-20 inspection incident

During post-v3 DEV diagnosis, the project task manifest `evals/tasks/e1b_candidates.jsonl` was read as a whole instead of reading only the DEV rows. That manifest contains the six nominal TEST task fixtures. No TEST task was executed, no TEST grader outcome was produced, and the live v3 experiment itself records `test_outcomes_opened=0`; however, the nominal TEST fixture content was exposed to the research/operator context.

Research consequence: the original six-task cohort can no longer be described as strictly model/operator-blind for any protocol changes made after this incident. It must not be used as clean confirmatory evidence for v4 or later prompt/protocol tuning. Existing pre-incident claims about zero TEST executions remain true, but `sealed` must be qualified as **not executed, fixture confidentiality compromised after v3**.

Containment:

- v4 changes are limited to generic DEV-derived failure classes: companion-file completeness, unconditional mappings, destructive migration behavior, and counterexample-oriented review. No TEST-specific rule, filename, symbol, expected value, or grader condition is encoded in v4.
- do not execute the original six TEST tasks as confirmatory evidence for v4+;
- create a replacement held-out cohort whose task/fixture contents are not exposed to the tuning context before any final autonomous repair claim;
- keep the original six only as contaminated diagnostic material if they are ever used later, clearly separated from confirmatory results.

This incident is logged rather than silently preserving a false seal claim.
