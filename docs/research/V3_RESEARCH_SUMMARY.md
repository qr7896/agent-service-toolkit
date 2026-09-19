# V3 Research Summary

## Research Question
In a chronological coding-task stream where only past trajectories are visible, can reliability-aware experience memory reduce repeated failures or retrieval cost without increasing stale-memory harm?

## Why V2 Is Not Enough
V2 studies evidence sufficiency and structural escalation inside a task. It does not establish whether experience from earlier tasks improves later tasks. V3 therefore freezes the V2 mechanism and isolates cross-task experience memory as the intervention.

## Hypothesis and Frozen Mechanism
The candidate policy combines compatibility, deterministic reliability, commit-distance decay/abstention, lifecycle filtering, and strict chronological eligibility. Mechanism development is frozen; later changes are limited to correctness fixes.

## Data Contract
Each prospective trajectory needs an immutable ID, timezone-aware event time, source repository, execution-time commit, task and changed paths, outcome/evidence, retrieved experience IDs, and an explicit adoption-observation state. Missing provenance fails closed.

## Evaluation Arms
1. No memory. 2. Always-on Top-k memory. 3. Compatibility-filtered memory. 4. Reliability-aware memory with abstention/lifecycle filtering. Compared arms must use the same eligible past pool.

## Anti-Leakage Rules
Only strictly earlier trajectories are eligible; equal-time events are not past evidence; source-problem/commit aliases are blocked; lifetime usage feedback is excluded unless reconstructable at that historical time; missing commit distance abstains.

## Implemented
Schema v2, execution provenance capture, prospective readiness, chronological replay, reliability/lifecycle rules, ablation runner, counterfactual evidence-availability replay, collection/preflight gates, frozen pipeline smoke, experiment checklist, protocol manifest, and artifact audit are implemented. The focused V3 suite most recently passed 38 tests with 0 failures; that is engineering validation, not efficacy evidence.

## Not Yet Proven
No claim is made that V3 improves task success, reduces reads/tool calls, or prevents repeated failures. Synthetic smoke results prove connectivity only. Counterfactual-ready pairs show evidence availability, not causal effect. The historical eight trajectories lack execution-time commit provenance and are not valid prospective evidence.

## Current Gate
The desktop workspace now exposes a real Git root and HEAD, and the read-only collection preflight passes. The cohort marker is intentionally not created until the frozen mechanism is committed and the first non-sealed task runner, model, and budget are fixed.

## Exact Next Experiment
Commit the frozen mechanism, rerun preflight from the clean checkout, select a non-sealed task runner and explicit model budget, then create the cohort marker immediately before the first task. Collect real prospective trajectories without tuning the mechanism, followed by frozen arms and artifact audit.
