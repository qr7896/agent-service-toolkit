# Formal E1 Wave B Network Task Source Policy

Status: PROPOSED_NOT_ACTIVE_FOR_FROZEN_FORMAL_E1_WAVE_B
Date: 2026-09-22
Applies to: isolated Wave B curator only

> Change-control note: this source policy was written after the frozen Wave B selection protocol and after Wave A outcomes were available. The frozen protocol requires the same public-source curation route as the clean replacement cohort and states that any later change to candidate discovery creates a new selection-protocol identity. Therefore SWE-bench/BugsInPy discovery is not activated for the existing Formal E1 Wave B identity unless an independent provenance audit establishes that it is the same pre-outcome route. Until then, this document is a proposed source policy for an extension cohort or a newly disclosed selection identity, not authority to curate the frozen 18-task Wave B.

## Decision

Public network sources may be used to discover candidate repair tasks. Network retrieval is a curation input, not an experimental outcome and not permission to expose hidden task content to the tuning/editor context.

Preferred Python-first sources:

1. SWE-bench / SWE-bench Verified public task metadata and upstream GitHub repositories.
2. BugsInPy public bug database and upstream repositories.
3. Direct public GitHub repair commits discovered through the same public-source route used by the replacement cohort.

Defects4J is an acceptable secondary source for future Java/generalization work, but Formal E1 Wave B should remain compatible with the frozen Python-oriented execution/runtime assumptions unless the existing sealed harness already supports the candidate without changing the intervention/runtime identity.

## Eligibility remains unchanged

A network-discovered candidate is not admitted merely because a benchmark labels it a bug. The isolated curator must still verify every frozen Wave B condition:

- targeted Base-Fail on the exact base revision;
- independently verified Gold-Pass;
- executable sealed harness without provider/model calls;
- no duplicate issue/patch lineage within Wave B;
- no duplicate lineage/source commit with Wave A;
- no overlap with prior DEV/contaminated commits;
- task/tests/gold/grader remain sealed from tuning/editor context;
- overlap/contamination audit passes.

The first 18 candidates in recorded discovery order that pass all conditions are admitted. Rejections remain in the sealed curator audit with content-neutral reasons.

## Leakage rule

SWE-bench records can contain `problem_statement`, `patch`, `test_patch`, FAIL_TO_PASS and PASS_TO_PASS fields. Those fields may be used only inside the isolated curator/sealed harness as needed for reproducibility. Do not return them to the tuning/editor context. In particular, gold patches must never become editor evidence.

The tuning/editor context receives only the existing v10.7 content-neutral metadata allowlist.

## Reproducibility rule

Prefer sources with reproducible buggy/fixed revisions and explicit tests. For SWE-bench, use the official containerized evaluation/task-repository route where practical. For BugsInPy, use its buggy/fixed checkout and relevant-test workflow. A candidate that cannot reproduce Base-Fail/Gold-Pass in the curator environment is rejected rather than repaired ad hoc.

## Identity boundary

Using public network discovery does not authorize changes to model, editor prompt, runtime, retrieval policy, tool config, sandbox config, analysis code, arm, call ceiling, token ceiling, max output, thinking mode or retry policy.

Any source-route change that alters the already frozen deterministic discovery/selection semantics must create and disclose a new selection-protocol identity before live Wave B execution.
