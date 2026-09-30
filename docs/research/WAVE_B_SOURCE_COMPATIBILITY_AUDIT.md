# Formal E1 Wave B Source Compatibility Audit

Status: BUGSINPY_ROUTE_EVIDENCE_FOUND__SWEBENCH_NOT_ESTABLISHED
Date: 2026-09-22
Scope: candidate-discovery route only

## Question

Can the newly available SWE-bench / BugsInPy network candidate pools be used under the already frozen Formal E1 Wave B selection identity without changing that identity?

## Evidence in the tuning workspace

The frozen Wave B protocol requires the same public-source curation route used for the clean replacement cohort and states that any later change to candidate discovery creates a new selection-protocol identity.

The surviving clean-replacement handoff prompt establishes only that a fresh isolated curator selected executable public repository repair tasks with independently verified Base-Fail and Gold-Pass, lineage/source-commit exclusions, a hidden manifest, and a sealed bundle. It does not identify SWE-bench, BugsInPy, a benchmark dataset, a deterministic network query, repository enumeration rule, or another concrete discovery source/order.

The progress archive records that the isolated curator selected public repair commits, rejected two candidates whose base did not fail, and admitted tasks from more-itertools/more-itertools and jazzband/prettytable. That is evidence about the admitted cohort, not enough evidence to reconstruct the pre-outcome discovery route.

## Recovered curator-environment provenance

A content-neutral filesystem/remote audit of the preserved independent-curator work directory found a pre-existing Git checkout at `work/BugsInPy` with origin `https://github.com/soarsmu/BugsInPy.git`. The same preserved work directory contains the admitted source-repository checkouts `more-itertools` and `prettytable`, whose origins are their public upstream GitHub repositories. This is direct surviving evidence that BugsInPy participated in the isolated curator environment used for the clean replacement cohort; it is materially stronger than the tuning-workspace documentation alone.

No equivalent surviving evidence has yet established that SWE-bench or `swe-bench-tasks` participated in that pre-outcome curator route. Therefore BugsInPy and SWE-bench must not be treated as equally proven route-compatible.

## Recovered verification stream evidence

The preserved curator scripts expose the concrete candidate-verification stream used on 2026-09-20. `verify_candidates.ps1` contains an ordered 14-commit candidate list for `more-itertools`; `verify_prettytable.ps1` contains an ordered 4-commit candidate list for `prettytable`. For each candidate the scripts derive the parent revision, run targeted tests on the repair commit, check out the parent, restore only the test file(s) from the repair commit, and rerun the targeted tests. Separate regression scripts run the selected repair commits against the full pytest suite. Git reflogs independently preserve the same checkout activity and timestamps.

This recovers the historical verification order for the preserved repositories, but not the upstream mechanism that originally chose those repositories/commits. Therefore it is strong provenance for replaying the verification procedure and exclusions, not sufficient evidence to invent a new discovery universe after Wave A outcomes.

## Preserved curator timeline

Filesystem/Git metadata reconstructs a content-neutral execution timeline on 2026-09-20: BugsInPy Git config was created at 18:40:48 +08:00; more-itertools at 18:41:40; `verify_candidates.ps1` at 18:47:12 and last written at 18:50:13; `verify_regressions.ps1` at 18:51:57; prettytable Git config at 18:56:27; `verify_prettytable.ps1` at 19:00:20 and last written at 19:03:14; `verify_prettytable_regressions.ps1` at 19:03:47; `build_sealed_bundle.py` at 19:07:04; and `run_pilot.py` at 19:07:44. The PowerShell PSReadLine history contains no matching clone/discovery commands, so it does not recover the missing upstream discovery query.

This timeline shows BugsInPy was acquired before both admitted source repositories and before candidate-verification scripts were created. It supports BugsInPy as contemporaneous curator input/context, but still does not prove a deterministic mapping from BugsInPy to the more-itertools/prettytable candidate streams.

## Reflog-recovered scan boundary

Git reflogs recover a broader pre-verification scan than the final verification scripts. The more-itertools clone event is preserved at 18:41:44 +08:00. At 18:49:21-18:49:45 the curator checked out an alternating sequence of repair candidates and neighboring/non-selected commits before returning to `master`; this sequence includes the later verified candidates plus additional commits not carried into the verification script. The prettytable clone event is preserved at 18:56:31; at 19:00:30-19:01:15 the curator repeatedly scanned a sequence containing the later verified repair candidates plus intervening commits before returning to `main`.

This proves that the final 14+4 verification lists were downstream of an earlier repository-history scan and were not the complete discovery universe. The exact command/query that generated the scan is still absent. Consequently Wave B must not define its new universe by treating the final verification list itself as the historical discovery rule.

## Observable discovery-filter hypothesis

A content-neutral comparison against repository history supports a narrower hypothesis about the missing scan filter: many commits that later entered verification have repair-oriented commit subjects and modify tests, while the broader histories also contain test-only, documentation, formatting, CI, typing, and refactor commits that were not carried forward. Examples in more-itertools include later-verified repair subjects such as fixes for `running_min`/`running_max`, empty `interleave_evenly`, reversed empty `numeric_range`, iterator/repeat behavior, and invalid exceptions; prettytable similarly contains later-verified repair subjects for `horizontal_align_char` and `add_rows()`.

This is evidence for a repair-commit-plus-test-change heuristic, not proof of the historical query. It must not be promoted to the frozen Wave B selection rule without a disclosed replay-boundary decision. It can, however, be used as an auditable candidate-generation hypothesis for a separately identified replay/extension cohort.

## Decision

BugsInPy compatibility is supported at the source-route level by surviving isolated-curator provenance: the preserved curator work directory contains the BugsInPy checkout alongside the repositories used for the admitted replacement cohort. This supports continuing Wave B discovery through the BugsInPy public-source route, subject to replaying the original deterministic ordering/filter or conservatively freezing a replay rule that does not use Wave A outcomes.

SWE-bench compatibility remains NOT ESTABLISHED for the existing frozen Wave B identity. Do not activate SWE-bench for that identity merely because it is a public repair-task source.

No task statements, source excerpts, tests, gold patches, graders, outcomes, prompts/responses, or task-specific hidden content may cross the curator boundary. SWE-bench remains suitable for a separately frozen extension cohort or a newly disclosed selection identity.

## Allowed provenance request

Request only content-neutral route metadata from the isolated curator:

- source type / public host;
- repository-discovery mechanism;
- deterministic ordering rule;
- query or enumeration rule if one existed before outcomes;
- timestamp or frozen artifact hash establishing pre-outcome use;
- whether the route can be replayed without Wave A outcomes;
- whether SWE-bench/BugsInPy was part of that route.

Do not request candidate identities, rejected-task identities, task text, tests, gold artifacts, grader details, or outcomes.

## Current technical evidence kept separate

The WebCodex runner can reach and shallow-clone the public SWE-bench task repository through Git transport. Its observed source HEAD and task-tree inventory are acquisition evidence only. They do not establish compatibility with the frozen Wave B selection identity and therefore do not authorize Wave B curation from that pool.
