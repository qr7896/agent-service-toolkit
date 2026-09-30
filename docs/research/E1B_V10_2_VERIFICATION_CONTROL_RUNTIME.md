# E1-B v10.2 Verification Control Runtime — Offline Synthetic Simulator

Date: 2026-09-20  
Schema: `e1b-verification-control-runtime-v1`  
Status: synthetic control-plane validation only.

## Purpose

v10.2 connects the frozen v10 Semantic Evidence IR and v10.1 Decision Policy into a deterministic bounded runtime:

`Evidence Acquisition → IR Verification → Decision → Escalation → BLOCK_PATCH / ALLOW_VERIFICATION`

It does not call a model, execute a patch, inspect hidden tasks, or measure repair efficacy.

## Runtime invariants

Runtime state records step, escalation usage, evidence IDs, evidence manifest and terminal action. Evidence acquisition is a deterministic fixture indexed by escalation round.

Two independent bounds prevent loops:

- v10.1 `MAX_ESCALATIONS=2`;
- v10.2 `MAX_STEPS=5`.

Contradiction terminates immediately. Unsupported requests more evidence. Ambiguity requests structural escalation. If later evidence resolves all obligations, the runtime may emit `ALLOW_VERIFICATION`. Exhausted escalation budget or max steps emits `BLOCK_PATCH`.

## Auditability

Every transition records action/reason, dominant disposition, evidence IDs/collisions, escalation state, and before/after evidence manifest hashes. Final trace SHA256 contains no timestamps or randomness.

Evidence IDs are deduplicated. If the same evidence ID carries conflicting records, the collision is explicit and routed as ambiguity rather than silently overwriting provenance.

## Claim boundary

`ALLOW_VERIFICATION` means only that the synthetic control plane would permit downstream testing/execution. It is not a PASS result, patch correctness result, repair success, or evidence of improved cost/success.

The simulator validates state-machine properties and auditability on synthetic/public generic fixtures only.
