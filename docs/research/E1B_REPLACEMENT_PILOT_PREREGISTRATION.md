# E1-B Replacement Held-Out Pilot Preregistration

Status: **FROZEN / READY FOR EXACT-COMMAND AUTHORIZATION**  
Date: 2026-09-20  
Scope: cost-bounded 12-task clean pilot; this is not the 100–200 task E2 main study.

This document freezes the analysis plan before the first held-out provider call. It does not authorize execution and does not expose held-out task content, tests, graders, symbols, gold patches or outcomes.

## Immutable identities

- replacement cohort manifest SHA256: `006b96c6a9b106a79a06885e51bf619df5e5afe1d649d38f7df4429c8cac2a12`
- freeze manifest SHA256: `1494d741b0d3cb446f7669a94b54c2504fff1ffc6efe1644492ac990ebd1dc32`
- admission manifest SHA256: `43a949bdb733a55ea0dadaed7ec7dd8269fa1fca79768d70a32f57e12e1fbff6`
- experiment package manifest SHA256: `0f6846a989d3e0b2b17d0f9f90fcc9537ce31eb066a0e0bb8b109e14bd79f4d7`
- run ID: `e1b-8bbc8ba900559ce6`
- exact model/version: `deepseek-flash`
- editor prompt SHA256: `8c8efd931ac6aba69b0f6ad72a934766878711045aad858035db7d82128e17bb`
- combined runtime SHA256: `7bdffb2434ed4d906c6c1e0b4cb57d70248ab2cb830b29294f103110d7fa2daa`
- retrieval policy ID: `e1b-heldout-single-arm-evidence-v1`
- retrieval policy SHA256: `e7362bc85991b0882cb2b54b36b505e8866fc9c0ff18b79afb2353ccb0b10f92`
- tool config SHA256: `97373e9bf63b5950d07e7d716edbd4a7393d3dae95b844eaabb317892b3b7e04`
- sandbox config SHA256: `e0dd464ce91f77249a17cf3ca0658bb193c6bf04fec41deef9696e1c5dc67ecf`
- analysis script SHA256: `d2d5d8c72933eebe67cd1df654025bea088ca5fb62497c211cedbb268b51451e`
- experiment arm ID: `e1b-heldout-single-arm-evidence-v1`
- provider call ceiling: `12`
- provider token ceiling: `26400`
- model settings: one call per task, thinking disabled, maximum output `600`, no retries

## Cohort and intervention

The admitted cohort contains 12 tasks from two public repositories. Independent curation attests 12/12 Base-Fail and Gold-Pass, no source-commit overlap, and a passed overlap audit. All fixtures and outcomes remain inside the isolated curator task.

This is a single-arm autonomous repair pilot under one frozen evidence policy. It does not estimate an adaptive-versus-fixed acquisition effect and must not be presented as that comparison.

## Outcomes

Primary outcome: independently graded exact `resolved / 12`, also reported as pass@1.

Secondary outcomes: F2P, P2P, provider calls, input/output/total tokens, files/actions/read volume if emitted by the frozen harness, safety or overreach events, and the frozen failure taxonomy. Oracle/editability is diagnostic only and cannot substitute for autonomous repair success.

## Denominator, failures and stopping

All 12 admitted tasks remain in the denominator. Provider/model/infrastructure failures remain visible outcomes. There are no model retries, outcome-based exclusions, budget additions or post-outcome protocol changes.

Stop at the first reached ceiling: all 12 calls completed or 26,400 provider tokens consumed. Preserve partial artifacts if a ceiling or failure stops the run.

## Claim boundary

The result supports only an exact descriptive claim for this admitted 12-task, two-repository, single-arm pilot. It is not a population Autonomous Repair Rate, not evidence of adaptive acquisition superiority, and not the E2 main study. Repeated DEV, contaminated original-six TEST fixtures, synthetic verifier tests and Oracle results remain separate evidence classes.

