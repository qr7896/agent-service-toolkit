# E1-B v10.8 Experiment Package Builder and Dry-Run Audit

Date: 2026-09-20  
Schema: `e1b-experiment-package-v1`  
Provider ledger schema: `e1b-provider-ledger-v1`

v10.8 converts an `ADMIT_OFFLINE_READY` v10.7 result into deterministic immutable experiment metadata. It does not contain a provider client and cannot start a live experiment.

The package chains the v10.6 freeze-manifest hash, v10.7 admission-manifest hash, task-manifest hash, frozen identifiers (including `experiment_arm_id`), provider call/token ceilings, one-shot flag, required artifact contract, and provider-ledger schema. `run_id` is derived from stable package content rather than time or randomness.

The dry-run materializer creates metadata only: `experiment_package.json`, empty `provider_calls.jsonl` and `task_outcomes.jsonl`, `run_summary.json` with zero provider calls, and `artifact_audit.json` marked `DRY_RUN_ONLY`.

The post-run audit contract checks ledger schema, monotonic sequence/call indexes, run/model identity, token reconciliation, provider ceilings, required artifacts, task-outcome count, zero forbidden-source accesses, and unchanged package-manifest chain. `e1b_post_run_analysis.py` additionally requires one strict outcome row per admitted task, reconciles outcome calls/tokens to the valid ledger audit, preserves provider failures in the denominator, separates Oracle/editability from `resolved`, reports a fixed failure taxonomy and supports exact-ID paired deltas. Ledger metadata stores hashes and token/accounting data rather than prompts, responses, task text, hidden tests, gold patches, credentials, or secrets.

Claim boundary: experiment packaging and artifact-accounting reproducibility only; no repair efficacy, model quality, or benchmark-generalization claim.
