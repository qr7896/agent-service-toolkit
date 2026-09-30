# Formal E1 Wave B Replay-Boundary Protocol

Status: PROPOSED_PRE_CURATION_FREEZE
Date: 2026-09-22

## Purpose

The exact historical repository/commit discovery query used by the clean replacement curator is not recoverable from surviving artifacts. This protocol defines a transparent replay boundary rather than pretending the missing query was recovered.

## Replay candidate generator

For a separately disclosed replay identity:
1. use public upstream Python repositories only;
2. freeze repository identities and order before task execution;
3. enumerate non-merge commits in reverse chronological order at a frozen source HEAD;
4. retain commits modifying at least one Python production file and at least one test file;
5. retain subjects containing: fix, bug, regression, error, exception, crash, incorrect, wrong, fail, or issue;
6. preserve enumeration order; never reorder by difficulty, model suitability, expected outcome, or Wave A information;
7. exclude Wave A issue/patch lineage and source commits before execution;
8. pass candidates to the recovered Base-Fail/Gold-Pass verifier;
9. admit the first 18 eligible candidates.

## Verification rule

For candidate repair commit C with parent P: targeted regression tests must pass on C; on P with only the relevant tests restored from C the same tests must fail; C must pass the full regression suite and frozen overlap/contamination checks. No provider/model call is part of curation.

## Freeze requirements

Freeze and hash repository list/order, source HEADs, any time window, repair-marker vocabulary, path classifier, ordering rule, overlap exclusions, and verifier implementation before curation. Any later change creates another replay identity.

## Historical recovery validation

The first executable replay inventory recovered 12/14 historical more-itertools verification candidates within the first 25 generated candidates and 3/4 historical prettytable candidates within the first 25. Expanding more-itertools to 100 recovered `cca3294` at rank 29. `958990e` remains excluded solely because its subject (`Raise for negative slice sizes in sliced()`) lacks the current repair-marker vocabulary despite changing both production and test Python files. The missing prettytable candidate `cf5b167` is a merge commit and is therefore excluded by the current non-merge rule even though merge-aware diff metadata shows both production and test changes.

These misses are useful falsification evidence: the reconstructed heuristic is close but not identical to the historical scan. The replay rule must not be silently widened after observing these misses. Any decision to include behavior-oriented subjects such as `raise` or merge commits requires a new frozen replay identity before new cohort curation.

## Claim boundary

This is not the original frozen Wave B selection identity unless an independent methodological decision explicitly accepts the disclosed discovery-query deviation. Report it as a provenance-reconstructed replay. SWE-bench remains outside this replay unless separately frozen.
