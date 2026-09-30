# Formal E1 Wave B Pre-Live Seal Record

Status: OFFLINE_READY_AWAITING_EXPLICIT_LIVE_AUTHORIZATION
Date: 2026-09-22

## Frozen cohort

- task count: 18
- repository: `more-itertools/more-itertools`
- selection protocol SHA-256: `7bd230c46102a014da039c2981a36a01918ab5f47457e2be7b57e981987118f5`
- cohort manifest SHA-256: `5ec7cc0068a44e4e0d4a661fb3bd3bbd675687ae80e99e5c1e8a2d6994526986`
- Base-Fail attested: true
- independent Gold-Pass attested: true
- full regression: 18/18 passed
- exact Wave A source-commit overlap: 0
- within-Wave-B stable patch-id duplicate groups: 0

## Frozen intervention identity

- model: `deepseek-flash`
- editor prompt SHA-256: `8c8efd931ac6aba69b0f6ad72a934766878711045aad858035db7d82128e17bb`
- runtime SHA-256: `7bdffb2434ed4d906c6c1e0b4cb57d70248ab2cb830b29294f103110d7fa2daa`
- retrieval policy SHA-256: `e7362bc85991b0882cb2b54b36b505e8866fc9c0ff18b79afb2353ccb0b10f92`
- tool config SHA-256: `97373e9bf63b5950d07e7d716edbd4a7393d3dae95b844eaabb317892b3b7e04`
- sandbox config SHA-256: `e0dd464ce91f77249a17cf3ca0658bb193c6bf04fec41deef9696e1c5dc67ecf`
- analysis script SHA-256: `d2d5d8c72933eebe67cd1df654025bea088ca5fb62497c211cedbb268b51451e`
- arm: `e1b-heldout-single-arm-evidence-v1`
- ceiling: 18 provider calls / 39,600 provider tokens
- execution: one call per task, max output 600, thinking off, no retry

## v10.7 admission

- decision: `ADMIT_OFFLINE_READY`
- reason: `all_admission_checks_passed`
- freeze manifest SHA-256: `1494d741b0d3cb446f7669a94b54c2504fff1ffc6efe1644492ac990ebd1dc32`
- admission manifest SHA-256: `e099b7710766dd49f458912a86a31b3454ad79b3b7513bb12338834ad12f2fe6`
- starts experiment: false

## v10.8 package and dry-run audit

- run ID: `e1b-e1c703e774119fae`
- package manifest SHA-256: `ef72c199e209e5322c453cab5856db137e4169b91022053d2e20e79e76702109`
- five-artifact audit: PASS
- provider calls: 0
- provider tokens: 0
- task outcomes: 0
- `provider_calls.jsonl`: zero bytes
- `task_outcomes.jsonl`: zero bytes
- artifact audit status: `DRY_RUN_ONLY`

Dry-run artifact SHA-256 values:

- `artifact_audit.json`: `6eeb2600991697cc25053bf8287a5f5d6bbacc4ac7a0d66a6fb9093c81393ab2`
- `experiment_package.json`: `ac5985b5f5404d072eb9686ee655945fb217c014da359b4b79e6d935e74adfd0`
- `provider_calls.jsonl`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `run_summary.json`: `75abfd0d00a7d2b7b31224f94a8c3cedb5482cf839779f37a57733a2349c2561`
- `task_outcomes.jsonl`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## Authorization boundary

This record freezes offline readiness only. It does not authorize or start a provider/model call. Wave B live execution requires a separate explicit authorization for the exact live command under the 18-call / 39,600-token ceiling. No prompt, retrieval, runtime, policy, grader, selection, or budget tuning may be introduced between this seal and the live run.
