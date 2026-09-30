# E1-B Research Contribution Consolidation

Core question: how can a Coding Agent become more accurate while reading less irrelevant code, overreaching less, and producing decisions that are easier to verify?

## Contribution 1 — Evidence-sufficiency-aware acquisition control

Implementation: V2 stop/continue diagnostics, adaptive lexical-to-structural retrieval work, v10.3 deterministic acquisition planner and v10.4 policy interface.

Evidence level: deterministic/offline trajectories, synthetic protocol tests, and earlier non-sealed observational experiments. Strongest allowed claim: the project implements an explicit bounded acquisition-control formulation that can stop, continue, or structurally escalate under evidence/cost/safety state. Prohibited overclaim: learned optimal retrieval, causal repair improvement, or universal token reduction.

## Contribution 2 — Unified semantic evidence and fail-closed verification control

Implementation: v9-v9.3 bounded semantic analyzers; v10 Semantic Evidence IR; v10.1 decision policy; v10.2 control runtime.

Evidence level: synthetic/public generic tests and deterministic preflights. Strongest allowed claim: heterogeneous coverage/dataflow/helper evidence is normalized into explicit satisfied/unsupported/ambiguous/contradicted obligations and drives bounded fail-closed control. Prohibited overclaim: formal program verification, complete semantics, or proof that a patch is correct.

## Contribution 3 — Reliability invariants and reproducible experiment boundary

Implementation: v10.5 metamorphic invariants, v10.6 freeze manifest, v10.7 admission gate, v10.8 immutable experiment package/dry-run/post-run audit.

Evidence level: adversarial unit tests, deterministic hashes and offline audit. Strongest allowed claim: the experiment/control plane detects specified classes of drift, leakage, tampering, accounting error and protocol violation before/after a run. Prohibited overclaim: security proof, provider honesty proof, or repair efficacy.

## Contribution 4 — Trajectory-to-experience / memory as a separately falsifiable research line

Implementation/evidence: prospective non-sealed trajectories and the selected V3 paired Memory OFF/ON pilot. The selected n=3 pilot showed no observed success benefit and +369 ON tokens, with identical OFF/ON patches; the stop rule was applied.

Strongest allowed claim: memory was treated as a measurable intervention rather than assumed useful, and this small selected pilot found no observed benefit under its protocol. Prohibited overclaim: memory is generally useless or harmful.

## Research positioning

The defensible novelty is not “we invented evidence sufficiency” or “we invented CodeGraph.” The project contribution is the integration of evidence-state acquisition control, bounded semantic verification, explicit safety/cost constraints, and auditable experiment governance into one Coding-Agent runtime research program. External/held-out efficacy evidence is still required.
