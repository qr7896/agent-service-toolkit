# E1-B One-Shot Preregistration Template

Status: fill and freeze before the first confirmatory provider call. This template does not authorize execution.

## Immutable identities

- replacement cohort manifest SHA256: `<fill>`
- freeze manifest SHA256: `<fill>`
- admission manifest SHA256: `<fill>`
- experiment package SHA256 / run ID: `<fill>`
- exact model/version: `<fill>`
- editor prompt SHA256: `<fill>`
- runtime SHA256: `<fill>`
- retrieval-policy SHA256: `<fill>`
- tool-config SHA256: `<fill>`
- sandbox-config SHA256: `<fill>`
- analysis-script SHA256: `<fill>`
- experiment arm ID: `<fill; one immutable package per arm>`
- provider call ceiling: `<fill>`
- provider token ceiling: `<fill>`

## Frozen hypotheses and arms

Primary acquisition hypothesis: under the admitted replacement cohort and frozen budget, adaptive evidence acquisition changes autonomous task outcome and evidence/cost behavior relative to the frozen fixed-retrieval baseline. Report the direction from data; do not preregister a guaranteed improvement.

Frozen arms: `<list exact arms before execution>`. Any learned-policy arm is permitted only if its training data, checkpoint and features were frozen without replacement-heldout outcomes.

Memory and verification-control comparisons are separate interventions; do not silently combine them with the acquisition treatment unless the factorial design is frozen here.

## Outcomes

Primary: independently graded complete-cohort autonomous task outcome, reported as exact resolved/tasks and pass@1 when applicable.

Secondary: F2P/P2P, target/evidence coverage, Oracle/editability where separately defined, files/actions/read volume, provider calls, input/output/total tokens, wall time if reliably captured, and predefined safety/overreach events.

Oracle/editability is diagnostic and must never be substituted for autonomous repair success.

## Missing calls, failures and retries

Provider/model failures remain in the ledger and denominator according to the frozen analysis script. Retry policy: `<NONE unless a deterministic infrastructure-only retry rule is explicitly frozen here before execution>`. Never add budget or retry a failed task because its outcome is unfavorable.

## Exclusions

Only pre-outcome cohort-quality exclusions made by the independent curation process are allowed. After the first held-out outcome is visible, no task may be removed for difficulty, model failure, unexpected grader behavior or unfavorable result; any unavoidable invalidation must be reported transparently with the original denominator and reason.

## Analysis and stopping

Run the admitted cohort once under the frozen package. Respect call/token ceilings. Do not tune prompts, retrieval, verifier thresholds or policy using held-out outcomes. Report all frozen arms and all admitted tasks. Small samples receive exact descriptive counts and uncertainty where appropriate; do not claim statistical generalization without adequate design/power.

## Claim boundary

The experiment can support only claims defined by its admitted cohort, frozen arms and observed metrics. It does not retroactively validate repeated DEV results, contaminated original-six fixtures, or synthetic verifier tests as population efficacy evidence.
