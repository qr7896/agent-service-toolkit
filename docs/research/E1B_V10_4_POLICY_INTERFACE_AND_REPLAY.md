# E1-B v10.4 Acquisition Policy Interface + Counterfactual Replay

Date: 2026-09-20  
Status: offline baseline/evaluation harness only.

## Purpose

v10.4 freezes an interface between evidence acquisition control and the policy implementation. The current implementation is only the deterministic v10.3 baseline. A future learned rank/stop policy may implement the same pure interface without changing Semantic Evidence IR, verification decisions, or safety bounds.

## Runtime-safe features

Candidate features contain only information available at decision time: obligation-kind compatibility, prior-attempt flag, structural flag, deterministic protocol cost, unresolved disposition counts, and remaining acquisition budget.

A leakage audit rejects feature field names containing gold, grader, resolved, expected_patch, outcome, or test_result. This is a guardrail, not a proof against every possible semantic leakage channel.

## Counterfactual replay

Synthetic action-result fixtures can replay each admissible first action in an isolated arm. Reported metrics are limited to terminal control action, steps, deterministic protocol cost, and evidence count. Replay does not execute patches and has no repair-success metric.

## Dominance audit

The action set is inspected for actions that have identical capability/structural status but strictly higher protocol cost than another action. Such actions are reported rather than automatically removed, preserving the frozen action set for auditability.

## Claim boundary

This layer does not train a policy and does not establish that one acquisition strategy improves repair success, latency, token cost, or generalization. It makes the deterministic baseline swappable, leakage-auditable, and replayable before any learned-policy experiment.
