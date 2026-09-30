# E1-B v10 Control-Plane Consolidation Audit

Date: 2026-09-20

## Scope

This audit consolidates v10 through v10.8. No new verifier capability or experiment version is introduced. The control plane is treated as frozen except for concrete audit/reproducibility defects.

## Architecture

Semantic Evidence IR -> Verification Decision -> bounded Control Runtime -> deterministic Evidence Acquisition -> Policy Interface / Counterfactual Replay -> Protocol Invariants -> Freeze Manifest -> Experiment Admission -> immutable Experiment Package / Dry Run / post-run audit contract.

## Resolved findings

The consolidation pass found concrete audit-layer weaknesses in v10.8 and hardened them without changing verifier semantics: package metadata could be mutated after construction without an independent package verification step; dry-run materialization could overwrite existing experiment artifacts; ledger numeric fields accepted Python booleans/negative values and lacked explicit validation; ledger status and request/response manifest hashes were not validated; summary schema accepted untracked extra/missing fields; malformed audit inputs were not explicitly fail-closed. These now have explicit validation and adversarial tests.

Earlier consolidation work also corrected overly broad metadata substring checks that falsely rejected legitimate `editor_prompt_sha256` and `provider_token_ceiling` fields.

## Frozen claim boundary

These layers provide deterministic offline evidence representation, fail-closed verification/control decisions, bounded acquisition-policy plumbing, metamorphic protocol checks, reproducibility manifests, experiment-admission checks, and experiment artifact/accounting contracts. They do not establish repair success, semantic equivalence, causal improvement, learned-policy superiority, benchmark generalization, or memory efficacy.

## Remaining limitations

The semantic verifier is intentionally bounded and does not prove general program semantics or interprocedural correctness. v10.3 protocol costs are abstract units rather than latency/token/dollar measurements. v10.4 counterfactual replay is synthetic control-plane analysis. v10.5 invariants cover selected properties, not formal verification of the implementation. v10.6-v10.8 protect declared manifests and metadata contracts but cannot prove that an external provider or runner behaved honestly. Real provider/model experiments remain unexecuted under this phase.

## STOP rule

Do not add v10.9 or another control-plane module merely to expand architecture. New control-plane code is justified only by a reproducible defect, a preregistered experiment requirement that existing contracts cannot represent, or a safety/reproducibility invariant that cannot be expressed by strengthening existing layers. Otherwise the next phase is experimental evidence, not more infrastructure.

Any future live experiment still requires a passing freeze/admission/package chain and separate explicit authorization of the exact provider/model command.
