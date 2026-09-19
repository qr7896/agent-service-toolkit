# V2 Claim Matrix

Date: 2026-09-18

This table is the authoritative short-form boundary for resume/interview/paper wording until external validation changes it.

| Claim | Status | Evidence | Allowed wording |
|---|---|---|---|
| Safe evidence action space is explicit and fail-closed | supported | V2-0 schema/policy tests | implemented/frozen |
| Offline decision dataset is replay-ready | supported with scope | 221 records / 93 trajectories / 20 source problems | generic/supervised replay ready |
| IPS/SNIPS/DR causal evaluation is ready | **not supported** | propensities are derived/plumbing uniform | ips_ready=false |
| Contextual policy generalizes | **not yet supported** | internal behavior-cloning + LOGO only | descriptive internal robustness |
| Adaptive stopping removes redundant retrieval | supported on internal deterministic sample | 10/10 second continuations add zero unique evidence | internal deterministic evidence |
| Structural escalation universally beats lexical | **not supported** | matched 10-task sample only; query semantics differ | structural improved coverage in this sample |
| Filter V3 reduces actual provider tokens by 81.59% | **not supported** | regex proxy tokenizer | proxy-token volume -81.59% |
| Filter V3 preserves target coverage | supported on internal sample | 7/7 retrospective target coverage | internal retrospective coverage |
| Adaptive controller achieves 10/10 autonomous repair | **not supported** | constrained Oracle editor only | constrained-Oracle editability 10/10 |
| V2 is SERBench evaluated | **not supported yet** | upstream checkout unavailable | external-evaluation ready only |
| V2 outperforms MSS-Complement | **not supported** | no matched external experiment | complementary control problem |
| Test500 is authorized | **not supported** | example/Cal500/freeze incomplete | Test500 remains blocked |

## Current strongest defensible contribution

A runtime-observable, evidence-sufficiency-aware acquisition controller that separates three concerns:

1. stop redundant acquisition when current evidence is sufficient;
2. switch retrieval modality when lexical coverage is insufficient;
3. compress structural evidence before downstream consumption.

The current evidence is internal/deterministic plus constrained-Oracle editability. External benchmark validation remains required.

## Promotion rule

No claim moves from “not supported” to “supported” merely because another local metric is added. Promotion requires the missing evidence class named in the table (for example official external evaluation or non-Oracle downstream repair).
