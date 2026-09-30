# V3 Runtime Freeze — 2026-09-22

Status: **candidate frozen for clean-cohort validation**

## Frozen runtime

- bounded source excerpts
- structured exact edits
- executable hidden guard
- failure classification
- failure-class selective escalation
- maximum two provider calls per task
- 4,000-token task ceiling; 12,000-token six-task diagnostic ceiling
- localized escalation reserve: multiplier 1.0, max output 400
- deterministic patch application and re-grade

## Development evidence

`v3-prospective-compact-006` completed 6/6 with 7,950 provider tokens and no provider infrastructure interruption. First pass was 3/6; all three first-pass failures were salvaged by selective escalation.

This is development evidence, not confirmatory efficacy evidence. Tasks 04–06 informed runtime development and must not be reused to claim clean prospective performance.

## Freeze rule

Do not tune prompts, failure cards, evidence ranges, reserve multipliers, or task budgets from clean-cohort outcomes. Reproducible infrastructure fixes are allowed only if logged separately and do not alter the repair policy.

## Next gate

Build a new non-sealed cohort that did not participate in runtime development. Run the frozen runtime unchanged, audit artifacts and infrastructure attribution, then decide whether the evidence is sufficient to start Formal E2.
