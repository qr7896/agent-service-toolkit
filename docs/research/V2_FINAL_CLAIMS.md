# V2 Final Claims

Date: 2026-09-19
Status: **V2 FROZEN**

## SUPPORTED

- The runtime prototype can explicitly STOP or escalate from lexical to structural acquisition under cost/risk/redundancy accounting on the internal deterministic sample.
- On that 10-task sample, Filter V3 reduced structural evidence from 77 to 12 items and regex proxy-token volume from 402 to 74 while preserving retrospective target-path coverage 7/7 and constrained-Oracle editability 10/10.
- Official SERBench example integration and Cal500 evaluation ran through the upstream loader, validator, and scorer at commit `8c27a88e48dcbcd4a5745573c95937a4740f4406`.
- The frozen V2 supplied-candidate compatibility method has Cal500 `mss_complete@5/@8=0.062/0.078`, with 0 compatibility and inference failures.
- A single frozen Test500 prediction artifact contains 500/500 valid predictions and passed official strict validation.

## SUPPORTED WITH LIMITATIONS

- Internal adaptive structural escalation improves constrained-Oracle editability over repeat lexical (10/10 vs 4/10) only on a small deterministic sample. The editor is an upper-bound oracle.
- Cal500 exposes a real external transfer failure: direct acquisition STOP semantics over-abstain, and the one candidate-only correction remains below the deterministic lexical arm at MSS@8 (0.078 vs 0.118).
- Cal500 spans 174 repositories and Test500 is repository-disjoint, but there is no private Test500 score yet.
- Evidence proxy-token counts measure deterministic regex tokens, not provider tokenizer inputs or billing.
- Behavior-cloning agreement describes action imitation, not expected policy value.

## NOT SUPPORTED

- Evidence coverage is not repair success.
- Constrained Oracle results are not Autonomous Repair Rate or patch success.
- Proxy-token reduction is not provider prompt-token reduction.
- Behavior agreement is not policy value or causal improvement.
- Cal500 results are not Test500 results.
- External benchmark compatibility is not superiority over MSS-Complement.
- The project does not claim to be the first coding-agent evidence-sufficiency method.
- No claim is made that CodeGraph/Filter V3 improved SERBench core results; those components are outside the supplied-candidate track.
