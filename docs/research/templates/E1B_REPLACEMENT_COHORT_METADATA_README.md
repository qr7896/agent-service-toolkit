# Replacement Cohort Metadata Template

This directory contains a content-neutral handoff template for an independently curated replacement held-out cohort. The template mirrors the current v10.7 admission allowlist exactly; it is not a real cohort and its placeholder values must not be admitted.

The independent curation process owns task selection, quality review, duplicate/lineage checks, Base-Fail verification, independent Gold-Pass verification and the cryptographic task-manifest. The tuning/editor context receives only the completed metadata object after curation.

`task_count` must be the admitted cohort size. `repo_ids`, `commit_ids` and `curation_timestamps` identify provenance without revealing task content. `overlap_audit_passed` must be true and `source_commit_overlap` false after checking DEV and the contaminated original-six source commits. `manifest_sha256` commits to the hidden cohort manifest. The two attestation booleans must be true only after the corresponding independent checks actually occurred.

Do not extend this handoff with task descriptions, issue bodies, setup material, tests, gold artifacts, expected values, task-specific identifiers, grader information, outcomes, prompts/responses or credentials. If additional content-neutral metadata becomes necessary, change the admission schema deliberately before the cohort is opened; do not add ad-hoc fields after outcomes are known.

## Copy-paste prompt for a fresh isolated curator task

Use this only in a new task that does not inherit the tuning/editor conversation:

> Independently curate a 12-task clean replacement held-out pilot cohort for the E1-B Coding Agent experiment. Keep all task statements, source excerpts, tests, gold patches, symbols, graders and outcomes inside this isolated task; never return them to the tuning task. Select executable repository repair tasks with independently verified Base-Fail and Gold-Pass, no duplicate issue/patch lineage, and no source-commit overlap with `e1b-src-21` through `e1b-src-30` or these prior commits: `1df3c67`, `28ab094`, `28c6b12`, `3183ac9`, `39ffc20`, `3e7b27c`, `59e9bdd`, `5a14425`, `994fd72`, `cd6a3f3`, `d76338f`, `e196446`, `ead5691`, `fcbe49e`. Freeze a hidden manifest and sealed execution bundle, but do not run a model or reveal any outcome. Return only one JSON object matching `docs/research/templates/e1b_replacement_cohort_metadata.template.json`: task count, repository IDs, exact commit IDs, curation timestamps, overlap-audit result, hidden manifest SHA-256, Base-Fail attestation and independent Gold-Pass attestation. Do not add task-specific fields. Stop after emitting that JSON and a content-neutral statement that the sealed bundle remains available in this isolated task.

The 12-task size is a cost-bounded clean pilot, not the 100–200 task E2 main study and not a basis for broad statistical generalization.
