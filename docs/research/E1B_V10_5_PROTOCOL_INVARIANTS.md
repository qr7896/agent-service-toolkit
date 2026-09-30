# E1-B v10.5 Protocol Invariants / Metamorphic Validation

Date: 2026-09-20  
Schema: `e1b-protocol-invariants-v1`  
Status: offline protocol validation only.

v10.5 adds no new runtime capability. It freezes cross-layer safety properties spanning Semantic Evidence IR, verification decisions and deterministic acquisition control.

The invariant set checks: irrelevant evidence cannot unblock an explicit contradiction; adding contradictory evidence cannot improve a disposition into an allow decision; reducing remaining acquisition budget cannot unlock an action; an attempted action cannot be selected again; canonical evidence permutations preserve manifests/decision semantics; duplicate/conflicting provenance remains fail-closed; explicit contradiction terminates with BLOCK; and fully satisfied obligations permit only ALLOW_VERIFICATION under the existing claim boundary.

The report contains deterministic invariant IDs, boolean results, fixture hash and action-set manifest. It contains no repair-success or pass-rate metric.

This is metamorphic/control-plane evidence, not evidence of Coding Agent repair efficacy or causal performance improvement.
