# Formal E1 Wave A Post-Run Report

## Protocol identity

- run ID: `e1b-8bbc8ba900559ce6`
- experiment package SHA-256: `0f6846a989d3e0b2b17d0f9f90fcc9537ce31eb066a0e0bb8b109e14bd79f4d7`
- cohort manifest SHA-256: `006b96c6a9b106a79a06885e51bf619df5e5afe1d649d38f7df4429c8cac2a12`
- freeze manifest SHA-256: `1494d741b0d3cb446f7669a94b54c2504fff1ffc6efe1644492ac990ebd1dc32`
- admission manifest SHA-256: `43a949bdb733a55ea0dadaed7ec7dd8269fa1fca79768d70a32f57e12e1fbff6`
- model: `deepseek-flash`
- arm: `e1b-heldout-single-arm-evidence-v1`
- ceiling: 12 provider calls / 26,400 tokens
- execution: one-shot, no retry
- artifact audit: schema valid, 12 provider rows, 12 task rows

## Autonomous outcome

All 12 admitted tasks remain in the frozen denominator.

- resolved: **0/12**
- pass@1: **0/12**
- failure taxonomy: **7 provider_infrastructure_failure + 5 verification_failure**
- F2P aggregate: **0/18**
- P2P aggregate: **0/0** (no P2P cases represented by these outcome rows)

The 7 provider failures are retained as outcomes and are not retried or excluded.

## Oracle / editability diagnostics

- target coverage: **12/12**
- oracle_editable=true: **0/12** as recorded by the outcome artifact

Target coverage is a retrieval/evidence diagnostic and does not imply autonomous repair success.

## Retrieval / evidence

The frozen run reports target coverage for all 12 tasks. This does not overcome the autonomous outcome: none of the 12 tasks resolved. No outcome-driven retrieval/prompt/policy changes are permitted between Wave A and Wave B.

## Editor / reasoning

Five tasks reached provider status `ok` but ended in `verification_failure`. This is evidence that a successful provider response plus target coverage was insufficient for a verified repair in these five cases. No hidden reasoning-state claim is made.

## Regression

- aggregate F2P passed/total: **0/18**
- aggregate P2P passed/total: **0/0**

The current artifacts therefore support failure-to-fix reporting, not a claim about P2P regression frequency.

## Cost

- provider ledger rows: **12**
- provider status `ok`: **5**
- provider status `provider_error`: **7**
- total provider tokens: **5,007**
- protocol token ceiling: **26,400**
- mean tokens per admitted task: **417.25**
- mean tokens per provider-ok task: **1,001.4**

The seven provider-error rows record zero tokens. No retry budget was added.

## Safety / overreach

- forbidden source accesses: **0**
- safety events: **0**

No safety/overreach event is recorded in the frozen Wave A outcome artifacts.

## Missingness and deviations

Before the completed live run, the exact command was started once and interrupted before any provider call because Git CLI was unavailable on the execution host. The partial directory contained the package and two zero-byte ledgers only: 0 provider calls, 0 tokens, 0 outcomes. It was preserved as:

`e1b-preprovider-interruption-8bbc8ba900559ce6-20260922-200951`

After Git for Windows was installed, the same frozen intervention/runtime identities were used for the completed run. The completed run exited 0 and produced the exact five-artifact contract. This infrastructure interruption is disclosed and is not counted as a task attempt.

The completed run itself contains 7/12 provider infrastructure failures. Under the preregistered denominator/no-retry rule they remain in the Wave A result.

## Claim boundary

Wave A is a negative/null autonomous held-out result: **0/12 resolved** for this admitted 12-task cohort under the frozen configuration. It simultaneously shows 12/12 target coverage and zero recorded safety events, but neither fact is repair efficacy. Seven provider failures create substantial infrastructure missingness/noise and are retained in the denominator rather than repaired post hoc.

Wave A must not be used to tune the frozen Wave B intervention. Wave B proceeds unconditionally under the selection protocol frozen before Wave A outcomes were observed.
