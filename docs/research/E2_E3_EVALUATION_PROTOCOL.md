# E2 / E3 End-to-End Evaluation Protocol

## Gate

E2 and E3 are new research stages, not extensions of the closed V3 pilot. No real-model E2/E3 call is authorized by creating this protocol. E2 starts only after the autonomous editor/runtime configuration and task construction rules are frozen. E3 starts only after E2 is completed and interpreted.

Execution schedule, minimum-scope budget and WebCodex handoff steps are maintained in `E1_E2_FAST_COMPLETION_PLAN.md`. That plan does not replace this protocol or authorize live calls; any proposed E2 go threshold or reduced-cost matrix must be frozen in an amendment before the first E2 provider call.

## E2 Main: 100–200 tasks

Purpose: paired comparison of retrieval/evidence policies under one fixed editor/runtime.

Arms: Fixed-K lexical baseline; V0 Evidence Gate; V0 Utility Gate; frozen V1 rank/stop; frozen V2 evidence-sufficiency policy; V3 experience ON/OFF only where strict-past eligibility exists. Add No-RAG, lexical-only, semantic-only, No-CodeGraph and No-Experience as predeclared ablations.

Controls: same coding model/version, editor prompt, tools, sandbox, max files written, per-task call/token/time ceilings and grader. Retrieval/experience policy is the manipulated variable. No arm receives extra retries or budget.

Sampling: 100–200 executable Base-Fail + Gold-Pass tasks, repository/commit grouped split, no issue variants across split, stratified by bug/feature/refactor, file count, cross-module depth and test type. Prefer temporal unseen commits. Record contamination risk.

Primary metrics: resolved/pass@1; F2P and P2P; input/output tokens; retrieval calls; files/unique files read; wall time; budget exhaustion; safety violations.

Research metrics: irrelevant-read ratio, Gold Evidence Recall, Evidence Precision, evidence sufficiency at STOP, redundant evidence, Editor/Reasoning Gap, Retrieval Gap and Regression Gap.

Statistics: paired task deltas with bootstrap 95% confidence intervals and effect sizes. Model/parse/budget failures remain outcomes and are not silently dropped. Report exact denominators.

Freeze artifacts before first call: task-manifest hash, base commits, environment/image hash, model id/version, editor prompt hash, tool/sandbox policy hash, each retrieval policy hash, token/tool/time ceilings and analysis script hash.

## E3 External: 300+ or public benchmark subset

Purpose: external validity across repositories and commits, not additional tuning.

Start condition: E2 is complete. E3 configuration is selected without inspecting E3 outcomes. Public benchmark contamination/training exposure is documented separately; temporal/live or newly curated tasks are preferred for the main claim.

Run one frozen configuration plus a small predeclared baseline set. Preserve trajectories, diffs, grader results and safety events. No per-repository prompt tuning or budget changes after outcomes are observed.

## Preflight checklist

- zero provider calls during dataset validation and manifest construction;
- Base-Fail + Gold-Pass verified independently;
- duplicate/source-commit/issue-lineage overlap audit passes;
- editor cannot access gold or hidden grader;
- all arms fit identical budget ceilings;
- deterministic scoring/analysis script tested on synthetic fixtures;
- manifest/config hashes written before live execution;
- explicit user authorization obtained for the exact live command and declared provider budget.
