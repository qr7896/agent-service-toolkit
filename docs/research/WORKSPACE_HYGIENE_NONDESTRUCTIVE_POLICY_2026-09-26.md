# Workspace hygiene — non-destructive policy (2026-09-26)

This repository contains a large amount of uncommitted research history. Generic Git hygiene
tools can misclassify experiment code, frozen manifests, tests, and audit artifacts as
temporary files. Therefore untracked does not mean disposable in this worktree.

## Safety rule

Until a separate archive/commit plan is explicitly approved:

- do not run git clean;
- do not bulk-delete untracked files;
- do not bulk-move historical experiment files;
- do not reset tracked modifications;
- do not stage or commit the entire dirty tree;
- do not rewrite old manifests/results merely to make the worktree clean.

## Classification

scripts/research_workspace_snapshot.py creates a hash-bearing inventory with five classes:

1. current_lineage — strict-v7 and the controlling strict-blind playbook; always keep.
2. historical_research — earlier experiment code/tests/docs; retain as lineage evidence.
3. generated_evidence — JSON/JSONL/CSV/results artifacts; retain as research evidence.
4. cache_or_runtime — runtime/cache material; review separately before any cleanup.
5. unknown — requires manual review; never delete based only on naming heuristics.

The snapshot is intentionally non-destructive: no file is moved, deleted, staged, committed,
or rewritten except the snapshot artifact itself.

## Recommended future cleanup

After the current strict-v7 mechanism is frozen, cleanup should be done by creating an
explicit archive manifest first. Only paths proven to be reproducible cache/runtime
artifacts should be candidates for deletion. Historical experiment code, preregistration
documents, manifests, ledgers, result summaries, and tests should be archived or committed,
not silently removed.
