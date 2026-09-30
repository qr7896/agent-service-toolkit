# E1-B / R10 v5 DEV Result

R10 v5 is a DEV-only preservation-first protocol iteration. It was run only after explicit authorization for `python -m evals.e1b_run_dev_live_v5`. The original E1-B TEST outcomes were not executed or opened by this experiment.

## Result

The run completed all four DEV tasks with 8 provider calls and 5,707 total tokens. There were zero parse failures, model failures, or budget exhaustions. Two of four DEV tasks resolved. This is protocol-development evidence on a repeatedly used four-task DEV set, not an Autonomous Repair Rate estimate.

Relative to v4, the resolved set did not change. Async propagation and config/code budget remained resolved. Cross-module status still passes the target fix but fails the pending-state P2P regression. State-version still fails the target fix and the legacy false-state preservation check. There were no v4→v5 resolved-task regressions.

The v5 reviewer changed the async proposal, but the other three final patches were accepted unchanged. Cross-module status reproduced the same final patch as v4. State-version changed its final patch relative to v4 but retained the same failure class. This indicates that prompt-level preservation language alone did not remove the remaining editor reasoning gap.

## Decision

The predeclared 4/4 freeze gate is not met. Do not freeze v5, do not open the original TEST, and do not start a replacement held-out one-shot from this configuration.

The next useful work is offline: stop iterating generic reviewer prose and make the editor protocol explicitly represent state/value transformations or add deterministic contract extraction before the model call. Any v6 live DEV run requires a new exact authorization.
