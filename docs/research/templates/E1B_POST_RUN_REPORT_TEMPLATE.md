# E1-B Post-Run Report Template

## Protocol identity

Record run ID, cohort/freeze/admission/package hashes, exact model/version, frozen arm, call/token ceilings and artifact-audit verdict.

Source the table only from the complete `task_outcomes.jsonl` plus a valid reconciled provider-ledger audit. Missing outcome rows, duplicate task IDs, arm/run drift, token drift, or invalid package identity are protocol failures, not exclusions.

## Autonomous outcome

Report admitted tasks, attempted tasks, resolved/tasks, pass@1 where applicable, F2P/P2P and failures. Keep infrastructure/model failures visible under the preregistered denominator rule.

## Oracle / editability diagnostics

Report Oracle editability or target coverage separately from autonomous outcomes. State explicitly that Oracle/editability does not equal repair success.

## Retrieval / evidence

Report retrieval actions, files/evidence items retained, target/evidence coverage, structural escalations, irrelevant-read proxy if preregistered, and evidence-sufficiency terminal states.

## Editor / reasoning

Report cases where sufficient/Oracle-editable evidence existed but the autonomous patch failed, using the frozen failure taxonomy. Do not infer hidden chain-of-thought or mental state.

## Regression

Report F2P/P2P and any post-patch regression category defined before the run. Distinguish inability to fix from breaking previously passing behavior.

## Cost

Report provider calls, input/output/total tokens, calls/task, tokens/task, wall time if reliably captured, and protocol-budget exhaustion. Keep abstract protocol cost separate from provider tokens/dollars/latency.

## Safety / overreach

Report forbidden-path attempts, sandbox/tool-policy violations, blocked unsupported actions, unnecessary writes if predefined, and false-block diagnostics where measurable.

## Missingness and deviations

List provider failures, missing artifacts, invalidated observations, retries (if any), protocol deviations and denominator effects. Reconcile ledger totals and package ceilings.

## Claim boundary

Separate autonomous held-out efficacy from Oracle/editability, retrieval diagnostics, software-regression tests and synthetic control-plane validation. Report null/negative findings and do not generalize beyond the design/population supported by the admitted cohort.
