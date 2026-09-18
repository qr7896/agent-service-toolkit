# E1-B Task Expansion Specification

## Goal

Expand the executable pool from 20 to at least 30 tasks without duplicating existing task logic. New tasks are benchmark data, not training examples for frozen V1. They must be kept outside the frozen V1 test result and receive a new E1-B manifest/split before comparison.

## Required new failure families

| Family | Minimum | Structural requirement |
| --- | ---: | --- |
| multi-file dependency | 2 | Gold repair changes at least two Python source files |
| cross-module call chain | 2 | failure is observed through a caller in another module |
| async/state boundary | 2 | async behavior or persisted/resumed state is essential |
| retrieval hard-negative | 2 | plausible same-name/same-keyword distractor file exists |
| config + code | 1 | repair requires both configuration and implementation evidence |
| regression trap | 1 | at least two PASS_TO_PASS nodes protect existing behavior |

These minima total 10 tasks. A task may carry multiple tags, but the 30-task milestone requires at least 10 distinct new instance IDs.

## Admission gate

Every candidate must satisfy all of the following before freeze:

1. Unique instance_id and source_commit identifier.
2. Non-empty problem_statement, FAIL_TO_PASS and PASS_TO_PASS.
3. Base workspace is unresolved.
4. Gold workspace is resolved.
5. Gold files and Gold sources are consistent.
6. No source-commit overlap with the final held-out comparator split.
7. No trivial clone of an existing task with only renamed symbols/constants.
8. Failure-family tags and structural statistics are recorded.
9. Autonomous Editor must not see Gold sources or Gold evidence labels.
10. Oracle Editor and Autonomous Editor results are reported separately.

## Difficulty statistics to freeze

For every task record: source-file count, Gold-file count, test-node count, number of modules touched, async flag, stateful flag, distractor-file count, and PASS_TO_PASS count.

The E1-B manifest should report distributions rather than only task count. This prevents reaching 30 tasks by adding ten equivalent single-function fixes.

## Claim boundary

The original 20-task pool remains useful for harness validation and diagnostics. The four-task V1 frozen subset remains the only currently opened held-out V1 test. E1-B is a new benchmark stage and must receive a new freeze boundary; it must not be described as an untouched V1 test.
