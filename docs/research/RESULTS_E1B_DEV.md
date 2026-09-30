# E1-B Autonomous Editor DEV Results

> Updated 2026-09-20. Scope is DEV only. The six E1-B TEST outcomes remain sealed.

## R10 v2: valid failed DEV

The budgeted R10 v2 run completed all four DEV tasks with four model calls and 2,305 provider tokens. The provider ledger/call path stayed within the declared budget, with zero parse failures, zero model failures, and zero budget exhaustions. This establishes that the budget/call-chain repair worked for this DEV run.

The editing result did not meet the freeze gate: 0 of 4 DEV tasks resolved. This is recorded as a **valid failed DEV result**, not as an Autonomous Repair Rate conclusion. The deterministic audit artifact is `evals/results/e1b_autonomous_dev_v2_audit.json` and reports `status=valid_failed_dev`, `budget_and_call_chain_valid=true`, and `freeze_ready=false`.

Compared with the earlier budget-invalid DEV run, async-propagation changed from resolved to unresolved. config-code-budget remained unresolved with the same patch hash. cross-module-status still repaired FAIL_TO_PASS but regressed a PASS_TO_PASS case. state-version remained unresolved with both the target behavior and one regression condition failing. These transitions move the bottleneck from provider-budget enforcement to editor reasoning/edit completeness.

## Protocol response

R10 v2 is archived unchanged. It is not overwritten, retried, or promoted into TEST.

The next DEV candidate is R10 v3, implemented separately in `evals/e1b_run_dev_live_v3.py`. It keeps the same Gold-hidden, sandboxed, declared-seed evidence boundary but changes the editor protocol rather than the grader:

- proposal prompt explicitly checks every supplied evidence item and companion file;
- a second bounded reviewer call receives only the public task, the same evidence, and the candidate patch;
- reviewer is instructed to catch missing companion-file edits, state/value mapping errors, async error handling mistakes, and visible-code regressions;
- maximum calls per DEV task becomes 2, with 600 output tokens per call, 4,000 task ceiling, and 16,000 total ceiling;
- v3 writes to new result/ledger paths and refuses overwrite/rerun.

The v3 zero-provider-call preflight is ready. Proposal reserves are 1,886–2,200 tokens. A deliberately oversized candidate-patch proxy keeps review reserves at 3,492–3,808, below the 4,000 task ceiling for all four DEV tasks. Focused E1-B + provider-budget regression is 34 passed.

## Freeze gate

R10 v3 is **DEV-ready, not TEST-ready**. A future live DEV v3 run requires explicit authorization because it performs real model calls. TEST remains sealed until a new DEV result passes artifact audit and the final editor/model/evidence/tool/budget/sandbox configuration is frozen.

## R10 v3: valid partial DEV

The authorized live v3 run completed all four DEV tasks with 8 model calls and 5,311 provider tokens. There were zero parse, model, or budget failures. One DEV task resolved end-to-end; three remained unresolved. The deterministic audit records `status=valid_partial_dev`, `protocol_valid=true`, and `freeze_ready=false`. The reviewer changed the candidate patch on one task, which is also the task that moved from v2 unresolved to v3 resolved; this is useful DEV evidence for the two-pass idea, but not a causal or population-level success claim.

The remaining DEV failures still fall into edit-completeness / semantic-regression classes: one F2P miss, one F2P-pass/P2P-fail case, and one task with both target and regression failure. Therefore v3 is archived and not frozen.

## R10 v4: contract + counterexample review

A separately versioned v4 candidate now reconstructs a behavioral contract before editing and makes the reviewer mentally simulate the stated failure, an unchanged ordinary case, a boundary/alternate state, and every visible companion file. It explicitly rejects one-branch special cases, unconditional mappings, destructive migrations, and runtime-only fixes that leave contradictory visible configuration unchanged. These are generic rules derived from the DEV failure classes, not task-specific answers.

v4 was then run once on all four DEV tasks. It completed 8 calls / 5,789 tokens with zero parse, model, or budget failures and resolved 2/4 tasks. async-propagation remained resolved; config-code-budget improved from v3 unresolved to resolved; there were no v3→v4 resolved regressions. cross-module-status still passes F2P but fails the pending-state P2P case, while state-version still fails its target behavior and one old-state preservation case. The deterministic audit records `status=valid_partial_dev`, `protocol_valid=true`, `freeze_ready=false`. The reviewer changed zero proposal patches in v4, so the observed gain cannot be attributed to reviewer correction; the stronger contract-oriented proposal is a plausible mechanism but is not established causally by four DEV tasks.

## Seal-integrity incident

Post-v3 diagnosis accidentally inspected the whole E1-B candidate manifest, which includes nominal TEST fixtures. No TEST task was executed and no TEST outcome was opened, but fixture confidentiality is no longer clean for protocol changes after v3. The original six must therefore not be used as clean confirmatory evidence for v4+. See `E1B_SEAL_INTEGRITY.md`. A replacement held-out cohort is required before a final autonomous repair claim.

## Claim boundary

Supported: v2 resolved the budget/call-chain failure; v3 resolved 1/4 DEV; v4 resolved 2/4 DEV under a protocol-valid run and improved one task without regressing the previously resolved task. v4 still fails the predeclared 4/4 freeze gate.

Not supported: 2/4 is a population Autonomous Repair Rate; the prompt change causally doubled success; the reviewer adds value in v4; memory/retrieval efficacy follows from these four tasks; or clean held-out performance is known.
