# E1-B R10 v8 DEV Result — State-Transition Gate

Date: 2026-09-20

## Scope
Repeated 4-task DEV only. Original contaminated TEST fixtures were not executed and replacement held-out outcomes remained unopened. This is protocol-development evidence, not a population repair-rate estimate.

## Frozen mechanism
v8 retained the v7 participant Coverage Gate and added frozen `e1b-state-transition-v1`. Proposal and final patches had to pass Coverage then State-Transition verification before apply/grade. Freeze criterion remained 4/4 resolved + protocol valid + no regression.

## Live result
Protocol valid=true; freeze_ready=false; status=`valid_regressed_dev`. Four tasks were attempted, 0 resolved, using 6 model calls and 5,391 tokens. There were no parse/model/budget failures and `test_outcomes_opened=0`.

### async-propagation-22
Two calls, 1,708 tokens. Proposal/final passed both gates; reviewer did not change the proposal; F2P failed while P2P passed. The v8 patch hash differs from successful v7b. This task has no explicit transition obligations, so the new transition gate did not reject or constrain it. The regression is consistent with editor-output variation under unseeded calls; this run does not establish a causal gate effect.

### config-code-budget-25
One call, 892 tokens. Proposal was rejected by the existing Coverage Gate because it omitted `config/retrieval.json`. v7b had produced both required participants and resolved. The transition gate was never reached. This is an editor participant-omission event caught fail-closed by v7 coverage logic, not evidence that the v8 transition mechanism caused the omission.

### cross-module-status-26
Two calls, 1,961 tokens. Both gates passed proposal/final. F2P and ordinary regression passed, but pending-state preservation failed. This is a false-accept boundary: static guarded witnesses for the extracted states passed while runtime preservation remained wrong. Guarded static witnesses are necessary-condition evidence only, not semantic equivalence.

### state-version-29
One call, 830 tokens. Coverage passed, but the transition gate rejected the proposal because the required identity witness for `version:2` was absent. No review/apply/grader followed. This is a fail-closed detection event. Because the rejected patch was not graded, it cannot be counted as a repair success or failure caused by the gate.

## Post-run observability issue
Gate-rejection rows stored exception text but not the complete rejected gate audit because `require_*` raised before returning it. The historical v8 result remains unchanged. Future protocol code now attaches the deterministic audit to the typed gate exception and would persist it as `rejected_gate_audit`. This is an observability fix only; v8 is not rerun.

## Decision
Do not freeze v8 and do not tune it further against these four DEV tasks. Preserve it as a negative/diagnostic result. Any semantic verifier successor should receive a new version (for example v9), be designed from public/synthetic cases, and have its specification frozen before evaluation. Clean confirmatory claims still require the replacement held-out protocol.
