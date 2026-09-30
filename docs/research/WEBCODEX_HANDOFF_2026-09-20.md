# WebCodex Handoff — E1-B Replacement Pilot

Date: 2026-09-20  
Current gate: **READY FOR EXACT-COMMAND AUTHORIZATION; live run not started**

## Copy-paste prompt for WebCodex

> Continue the research project from `docs/research/WEBCODEX_HANDOFF_2026-09-20.md` and execute the ordering in `docs/research/E1_E2_FAST_COMPLETION_PLAN.md`: E1快速封板 → E2保质量快速结束 → E3按30/100/300阶段推进并允许按预注册规则提前停止。Preserve v10-v10.8 and the preregistered 12-task pilot as frozen. First run only non-model consistency checks/tests and report the result. Do not inspect any sealed/hidden task material, do not call a provider, and do not change prompt/config/budget/analysis identities. The desktop-only live command requires a separate exact authorization and must not be reconstructed or run in WebCodex. Keep logs centralized in `docs/research/PROGRESS_LOG_ARCHIVE.md` and current status concise in `docs/PROGRESS_RESEARCH_ROADMAP.md`.

## Start here

Read, in order:

1. `docs/research/E1_E2_FAST_COMPLETION_PLAN.md`
2. `docs/research/E1B_REPLACEMENT_PILOT_PREREGISTRATION.md`
3. `docs/research/E1B_EXPERIMENT_READINESS_CHECKLIST.md`
4. `docs/research/E1B_REPLACEMENT_HELDOUT_PROTOCOL.md`
5. `docs/research/E1B_OFFLINE_DRY_RUN_OPERATOR_CHECKLIST.md`
6. `docs/research/PENDING_E1B_AUTONOMOUS_TESTS.md`

## Completed and verified

- Independent projectless curator produced a sealed 12-task cohort across two public repositories.
- 12/12 targeted Base-Fail and independently attested Gold-Pass; overlap audit passed; source-commit overlap is false.
- Tuning workspace received only allowlisted content-neutral metadata. Do not request or inspect task statements, tests, gold patches, symbols, graders or outcomes.
- Real-metadata admission returned `ADMIT_OFFLINE_READY`.
- Final zero-call dry run: run `e1b-8bbc8ba900559ce6`, package manifest `0f6846a989d3e0b2b17d0f9f90fcc9537ce31eb066a0e0bb8b109e14bd79f4d7`.
- Dry-run directory contains exactly the five required artifacts; both JSONL ledgers are empty; summary is 0 calls / 0 tokens; audit is `DRY_RUN_ONLY` and `starts_experiment=false`.
- The final experiment package was copied to the isolated curator output and source/destination file hashes matched.
- Desktop-local harness, sealed bundle, experiment package, tool config, sandbox config, prompt and provider adapter paths all existed at handoff time.
- Latest full non-model regression before metadata-only documentation changes: **617 passed / 4 skipped / 33 warnings**.

## What WebCodex can safely continue

- Review documentation consistency and run non-model tests.
- Run `git diff --check` and focused tests for the admission/package/post-run analysis modules.
- Prepare the post-run report shell without inventing results.
- Inspect only repository files and content-neutral metadata.
- After a desktop live run completes, analyze only the five declared artifacts with the frozen analysis script and update the report with exact counts.

## What WebCodex must not do

- Do not run a provider/model command without separate user authorization for the exact command.
- Do not open the original contaminated six TEST fixtures, replacement sealed bundle contents, hidden tests, gold patches, graders or private SERBench/Test500.
- Do not modify the frozen prompt, runtime, policy, config, analysis plan, ceilings or cohort after any held-out outcome is visible.
- Do not retry failed tasks, add budget, remove tasks from the denominator, or turn test counts/Oracle results into an Autonomous Repair Rate.
- Do not assume desktop-only paths, the isolated curator task or `DEEPSEEK_API_KEY` are available in a web environment.

## Desktop-only continuation

The live assets are outside this repository under the independent curator directory on the desktop. Therefore the one-shot run should remain a desktop action unless those exact immutable assets are deliberately made available to another trusted execution host without exposing their content to the tuning context.

Exact command awaiting separate authorization:

```powershell
& python "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\work\execution_interface\run_single_arm.py" `
  --sealed-bundle "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\outputs\e1b-heldout-pilot-sealed.zip" `
  --experiment-package "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\outputs\e1b-experiment-package.json" `
  --tool-config "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\work\execution_interface\tool-config.json" `
  --sandbox-config "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\work\execution_interface\sandbox-config.json" `
  --editor-prompt "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\work\execution_interface\editor-prompt.txt" `
  --provider-runner "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\work\execution_interface\deepseek_provider_runner.py" `
  --results-dir "C:\Users\qq人\Documents\Codex\2026-09-20\e1b-independent-curator\outputs\e1b-live-results-8bbc8ba900559ce6" `
  --confirm-live
```

Before execution, verify that `DEEPSEEK_API_KEY` exists without printing its value and that the results directory does not already exist. Execute once only after the user explicitly confirms this exact command. Do not auto-retry if the provider is unavailable or the balance is insufficient; preserve artifacts and report the interruption.

## After the one-shot run

1. Do not change or rerun the experiment.
2. Validate all five artifacts and reconcile task outcomes with provider calls/tokens.
3. Run the frozen post-run analysis.
4. Report exact `resolved/12`, pass@1, F2P, P2P, failures, calls and tokens; keep all 12 tasks in the denominator.
5. Update the preregistered report and centralized progress log. Keep claims within the pilot boundary.
