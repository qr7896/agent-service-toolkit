# Formal E1 Wave B Independent Curator Handoff

Status: READY_FOR_ISOLATED_CURATION  
Selection protocol: `E1_WAVE_B_SELECTION_PROTOCOL.md`  
Selection protocol SHA-256: `7bd230c46102a014da039c2981a36a01918ab5f47457e2be7b57e981987118f5`  
Target admitted cohort: 18 tasks

## Isolation requirement

Run this curation in a fresh isolated curator context that does not inherit Wave A experimental outcomes, generated patches, prompts/responses, or tuning discussion. The curator may inspect only the sealed Wave A provenance required to exclude duplicate lineage and source commits.

Do not expose task statements, source excerpts, tests, gold patches, symbols, graders, expected values, or task-specific identifiers back to the tuning/editor context.

## Copy-paste curator instruction

> Independently curate Formal E1 Wave B as an 18-task clean held-out cohort under the already frozen `docs/research/E1_WAVE_B_SELECTION_PROTOCOL.md` (SHA-256 `7bd230c46102a014da039c2981a36a01918ab5f47457e2be7b57e981987118f5`). Do not inspect or use Wave A experimental outcomes, generated patches, prompts/responses, or tuning signals. Use the same public-repository repair discovery route as the clean replacement cohort and record candidate discovery order inside the sealed curator manifest. Evaluate candidates in that recorded order and admit the first 18 that satisfy every frozen eligibility condition: targeted Base-Fail; independently verified Gold-Pass; executable sealed harness without provider/model calls; no duplicate issue/patch lineage within Wave B; no duplicate lineage with Wave A; no source-commit overlap with Wave A or prior DEV/contaminated commits; sealed fixture/tests/gold/grader/task text; overlap/contamination audit passed. Record rejected candidates and content-neutral rejection reasons inside the sealed audit, but do not count them in the denominator. If the initial repository set yields fewer than 18 eligible tasks, expand discovery using the same route/filter and record the expansion boundary before evaluating those candidates. Do not balance task types or replace candidates based on outcomes. Freeze the hidden 18-task manifest and sealed execution bundle. Do not call any model/provider. Return to the tuning context only one content-neutral JSON object with exactly these fields: `task_count`, `repo_ids`, `commit_ids`, `curation_timestamps`, `overlap_audit_passed`, `source_commit_overlap`, `manifest_sha256`, `base_fail_attested`, `gold_pass_independently_attested`. Also return only a content-neutral statement that the sealed bundle and curator audit remain available in the isolated curator context.

## Required returned metadata shape

```json
{
  "task_count": 18,
  "repo_ids": [],
  "commit_ids": [],
  "curation_timestamps": [],
  "overlap_audit_passed": true,
  "source_commit_overlap": false,
  "manifest_sha256": "<64-hex-sha256>",
  "base_fail_attested": true,
  "gold_pass_independently_attested": true
}
```

No additional task-specific fields are allowed.

## Frozen execution identity after curation

Wave B must reuse the Wave A intervention/control-plane identities:

- model: `deepseek-flash`
- editor prompt SHA-256: `8c8efd931ac6aba69b0f6ad72a934766878711045aad858035db7d82128e17bb`
- runtime SHA-256: `7bdffb2434ed4d906c6c1e0b4cb57d70248ab2cb830b29294f103110d7fa2daa`
- retrieval policy SHA-256: `e7362bc85991b0882cb2b54b36b505e8866fc9c0ff18b79afb2353ccb0b10f92`
- tool config SHA-256: `97373e9bf63b5950d07e7d716edbd4a7393d3dae95b844eaabb317892b3b7e04`
- sandbox config SHA-256: `e0dd464ce91f77249a17cf3ca0658bb193c6bf04fec41deef9696e1c5dc67ecf`
- analysis script SHA-256: `d2d5d8c72933eebe67cd1df654025bea088ca5fb62497c211cedbb268b51451e`
- arm: `e1b-heldout-single-arm-evidence-v1`
- Wave B ceiling: 18 calls / 39,600 tokens
- one call per task, max output 600, thinking off, no retry

Cohort/package/run identities are expected to be new. Do not alter the intervention identities above based on Wave A results.

## Next gate

After the isolated curator returns the content-neutral metadata, run v10.7 admission and v10.8 zero-call package/dry-run in a fresh output directory. Provider calls remain unauthorized until the resulting Wave B exact live command and budget receive separate explicit authorization.
