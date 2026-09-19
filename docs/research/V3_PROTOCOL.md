# V3 Protocol — Reliability-Aware Continual Experience Memory

## Material Passport

- Artifact type: code experiment plan
- Status: MECHANISM FROZEN / PROSPECTIVE DATA GATE
- Date: 2026-09-19
- Inputs: existing local trajectories, `agents.experience`, `agents.coding_memory`, V2 frozen boundaries
- External model/API use: none
- Protected data: internal E1-B sealed TEST remains closed

## Research question

In a chronological coding-task stream where only past trajectories are visible, does reliability-aware experience memory reduce repeated failures or retrieval cost without increasing stale-memory harm?

## Units and variables

- Unit: one source-problem execution at a fixed repository commit.
- Intervention: experience retrieval/adoption policy.
- Baselines: no memory; always-on Top-k; compatibility-filtered memory.
- Candidate method: reliability-aware retrieval with abstention and lifecycle filtering.
- Primary outcomes: independently graded task success, attempts, reads, tool calls.
- Secondary outcomes: retrieved/adopted/changed-decision counts, stale-memory harm, conflict and invalidation rates.
- Cost fields: proxy tokens and provider tokens are recorded separately; neither substitutes for the other.

## No-leakage protocol

1. Sort by execution event time; ties are resolved by immutable trajectory ID.
2. A task may read only experiences created strictly earlier.
3. Source problem and commit aliases may not cross the replay boundary as independent samples.
4. Outcome/test/review evidence may compile an experience after execution, but may not enter that execution's policy state.
5. Retrieval, adoption, and changed-decision are distinct events.
6. Test500 private certificates and internal E1-B sealed TEST are outside V3 development.

## Experience Schema v2 gate

Each compiled experience must carry:

- `schema_version`, `trajectory_id`, `source_repo`, `source_commit_at_execution`, `event_time`;
- accepted/rejected outcome and structured failure type;
- task signature, reuse constraints, action prior and validation strength;
- lifecycle state (`active/isolated/invalidated`) with reason and event time;
- usage counts for retrieved/adopted/helped/harmful;
- compiler/config hash.

Migration must write a new artifact; it must not overwrite the existing experience database.

## Execution order

1. V3-0 readiness audit.
2. Schema v2 + provenance capture.
3. Past-only chronological replay gate.
4. Deterministic reliability baseline and forgetting rules.
5. Retrieval/adoption ablation.
6. Negative-experience and counterfactual replay.
7. Only then consider a budgeted prospective/model experiment.

## Claim boundary

Until chronological paired evaluation exists, V3 may claim only schema/replay readiness. Retrieval hit rate, behavior agreement, and final task success without a memory counterfactual do not establish experience value.


## Replay feedback boundary

Untimestamped lifetime usage/help/harm counters are excluded from replay reliability by default. Usage feedback may enter a replay decision only through an explicitly past-visible snapshot. V3 mechanism development is frozen after V3-6; the next gate is prospective non-sealed data with execution-time provenance.
