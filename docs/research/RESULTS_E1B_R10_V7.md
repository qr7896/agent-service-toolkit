# E1-B/R10 v7 DEV result

Date: 2026-09-20

## Execution note

The first authorized v7 invocation was invalid before any provider call: the runner accidentally delegated to the v4 module invoke path, so it read the already-spent v4 ledger and failed with task call ceiling reached 2/2. It produced 0 provider calls / 0 tokens and is retained as evals/results/e1b_autonomous_dev_run_v7.json for provenance. It is not used as DEV evidence.

The plumbing bug was fixed by making v7 call budgeted_ainvoke with its own provider_config. A fresh run identity e1b-r10-dev-v7b and fresh result/ledger paths were used. Zero-call preflight was repeated before the live call.

## Valid v7b result

- 4 DEV tasks; 8 completed provider calls; 5,797 tokens.
- 0 parse/model/budget/contract-coverage failures.
- 2/4 resolved; test_outcomes_opened=0.
- deterministic audit: valid_partial_dev; protocol_valid=true; freeze_ready=false.
- v5 to v7b improvements: none; regressions: none.

async-propagation and config-code-budget resolved with F2P/P2P pass. cross-module-status remained unresolved with complete participant coverage: F2P passes but pending-state P2P fails. state-version remained unresolved with complete participant coverage: target F2P fails and legacy false-state P2P fails.

## Interpretation

The Coverage Gate prevents the v6 omission class at runtime and the config task returned to the v5 success state. It does not improve the two remaining behavioral-preservation failures. This separates file/participant completeness from state/value semantic preservation.

This repeatedly tuned four-task DEV set is protocol-development evidence only, not a population repair-rate estimate or causal estimate of general effectiveness. The predeclared 4/4 freeze gate is not met. Replacement held-out outcomes remain closed.
