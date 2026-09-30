# E1-B Future Live Command Authorization Handoff

The real 12-task pilot is now offline-ready. This document still does not authorize execution. The frozen identities, desktop-only paths and exact proposed command are recorded in `E1B_REPLACEMENT_PILOT_PREREGISTRATION.md` and `WEBCODEX_HANDOFF_2026-09-20.md`.

Before proposing any future provider/model command, record the freeze manifest SHA256, experiment-admission manifest SHA256, task-manifest SHA256, task count, repository/commit overlap audit, Base-Fail attestation, independent Gold-Pass attestation, model/version identifier, editor prompt SHA256, runtime SHA256, retrieval-policy SHA256, tool configuration SHA256, sandbox configuration SHA256, analysis-script SHA256, provider call ceiling, provider token ceiling, and one-shot frozen-config flag.

The overlap audit must pass. Both attestations must be true. Original contaminated TEST fixtures/outcomes, replacement held-out content/outcomes, repeated DEV outcomes, and private SERBench/Test500 remain excluded according to the protocol boundary.

Admission returned `ADMIT_OFFLINE_READY` for run `e1b-8bbc8ba900559ce6`, with zero provider calls. The user must explicitly authorize the exact command in `WEBCODEX_HANDOFF_2026-09-20.md` before it is run. Generic instructions such as “continue”, “run needed tasks”, or “start testing” are not exact-command authorization under the repository research-safety rule.
