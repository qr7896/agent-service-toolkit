# E1-B v10.3 Deterministic Evidence Acquisition Protocol

Date: 2026-09-20  
Schema: `e1b-evidence-acquisition-v1`  
Status: offline deterministic control policy only.

## Purpose

v10.2 validates a bounded verification control loop but receives pre-baked acquisition rounds. v10.3 adds a finite deterministic acquisition planner so unresolved obligations select a compatible evidence action rather than blindly requesting another round.

## Frozen action space

| Action | Cost | Capability |
|---|---:|---|
| lexical | 1 | identity/change |
| coverage_check | 1 | coverage |
| direct_ast | 2 | identity/change |
| helper_summary | 3 | identity/change |
| structural_escalation | 4 | coverage/identity/change ambiguity |

For unsupported obligations, the planner selects the cheapest compatible untried non-structural action. Failed actions are recorded and cannot repeat. For ambiguity, structural escalation is preferred instead of repeating lexical/direct checks. Contradiction bypasses acquisition and blocks.

If no compatible untried action remains, the planner returns EXHAUSTED.

## Independent cost bound

`MAX_ACQUISITION_COST=8` is independent of v10.1 escalation budget and runtime step bounds. An action that would exceed the cost budget is not executed; the runtime fails closed.

Costs are deterministic protocol units, not measured tokens, latency, dollars, or learned utility.

## Auditability

Each acquisition transition records action, protocol cost, cumulative cost, reason, unresolved obligation IDs, and before/after evidence hashes. Final trace SHA256 contains no timestamps or randomness.

## Relationship to V0/V1/V2

The action-space/cost framing resembles V0 utility control, V1 rank/stop, and V2 evidence sufficiency, but v10.3 is deliberately deterministic. It is not a learned ranker, does not reuse frozen DEV outcomes, and provides no efficacy claim.

The purpose is to make the verification control plane executable and auditable before considering any learned acquisition policy.
