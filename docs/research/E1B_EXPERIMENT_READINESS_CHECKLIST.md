# E1-B Experiment Readiness Checklist

Date: 2026-09-20

## DONE

- v10-v10.8 control plane consolidated and frozen; no v10.9 planned without a concrete defect or preregistered requirement.
- Semantic Evidence IR, verification decision, bounded runtime, deterministic acquisition baseline, policy interface/replay, protocol invariants, freeze manifest, admission gate, immutable package, dry-run and post-run audit contract exist.
- Latest verified code baseline: 617 passed / 4 skipped / 33 warnings.
- Reproducibility fix: every package freezes `experiment_arm_id`; the required artifact set includes `task_outcomes.jsonl`; the frozen analysis path rejects missing tasks, schema/identity drift, Oracle-as-success substitution and ledger/token mismatch.
- This phase made zero provider/model calls.
- Original six nominal TEST tasks were not executed; fixture confidentiality was compromised after v3, so they are not clean confirmatory evidence for later versions.
- Replacement held-out protocol exists and keeps task content/outcomes unavailable before freeze.

## EXTERNAL PREREQUISITES

- Curate an actual replacement held-out cohort outside the tuning loop.
- Supply content-neutral metadata only: task count, repo IDs, exact source commits, curation timestamps, overlap audit and task-manifest hash.
- Establish Base-Fail and independently verified Gold-Pass attestations without exposing hidden content to the editor/tuning process.
- Confirm no source-commit overlap with DEV or the contaminated original six.
- Freeze exact model/version, editor prompt, runtime, retrieval policy, tool config, sandbox config and analysis-script identifiers/hashes.
- Choose preregistered provider call/token ceilings and the final analysis plan.

Independent curation is complete: 12 tasks across two public repositories, 12/12 Base-Fail/independent Gold-Pass attested, overlap audit passed, and hidden manifest SHA-256 `006b96c6a9b106a79a06885e51bf619df5e5afe1d649d38f7df4429c8cac2a12`. Exact config and preregistration are frozen. Real-metadata admission returned `ADMIT_OFFLINE_READY`; the five-artifact dry run is valid with 0 calls / 0 tokens. Run ID is `e1b-8bbc8ba900559ce6`; package manifest is `0f6846a989d3e0b2b17d0f9f90fcc9537ce31eb066a0e0bb8b109e14bd79f4d7`. Current gate: `READY_FOR_EXACT_COMMAND_AUTHORIZATION`.

The tuning task stores only `e1b_replacement_cohort_metadata.json`; it has not read the sealed task fixtures, graders or gold patches.

## REQUIRES EXACT USER AUTHORIZATION

- Any command that invokes a real provider/model.
- Any one-shot replacement held-out experiment command.
- Any future command that consumes provider budget or opens model-generated experimental results.

Generic instructions to continue work are not exact live-command authorization. Passing `ADMIT_OFFLINE_READY` is protocol readiness only and never starts an experiment.
