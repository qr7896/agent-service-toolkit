# E1-B v10.1 Verification Decision Policy — Offline Candidate

Date: 2026-09-20  
Schema: `e1b-verification-decision-v1`  
Status: offline policy layer only; no provider/model calls or live runner.

## Purpose

v10 separates obligations from evidence and classifies each obligation as satisfied, unsupported, ambiguous or contradicted. v10.1 converts those dispositions into bounded runtime decisions without calling a model and without treating static verification as repair success.

Priority is frozen safety-first:

`contradicted > ambiguous > unsupported > satisfied`

Actions are:

- contradicted → `BLOCK_PATCH` immediately;
- ambiguous → `STRUCTURAL_ESCALATION`;
- unsupported → `REQUEST_MORE_EVIDENCE`;
- all satisfied → `ALLOW_VERIFICATION`.

`ALLOW_VERIFICATION` means only that downstream execution/testing may proceed. It is not PASS, patch correctness, or repair success.

## Evidence sufficiency

The policy records required/satisfied/unsupported/ambiguous/contradicted counts and required/satisfied counts by obligation kind. It intentionally has no learned or probabilistic confidence score.

## Bounded escalation

The offline policy freezes `MAX_ESCALATIONS=2`. Ambiguous or unsupported decisions consume one escalation unit. Once the budget is exhausted, the action becomes `BLOCK_PATCH` with reason `escalation_budget_exhausted`. Contradiction blocks immediately and consumes no escalation budget.

This prevents evidence acquisition from looping indefinitely.

## Connection to V2

V2 asked whether currently acquired evidence was sufficient to stop retrieval or whether structural escalation was warranted. v10/v10.1 applies the same broad control idea to verification evidence: unsupported evidence requests acquisition; ambiguous evidence requests structural disambiguation; contradiction stops the patch; sufficient non-conflicting evidence permits downstream verification.

This is an architectural connection, not evidence that the combined system improves repair success or cost.

## Auditability

Every decision has deterministic policy metadata, sufficiency accounting, escalation state and a SHA256 audit manifest. No timestamps or random values enter the hash.

Development and preflight use synthetic/public generic cases only.
