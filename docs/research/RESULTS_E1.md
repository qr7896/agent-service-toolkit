# E1 Results

## Scope

E1 separates retrieval sufficiency from autonomous editing ability. Stage 1 uses the exact four-task V1 frozen test subset with a constrained Oracle Editor. The Oracle may write Gold source only for files exposed by retrieval, and independent pytest grading determines resolution. This is a retrieval-to-editability upper-bound experiment, not autonomous Coding Agent success.

E1-B now contains a 30-task executable pool: the original 20 research tasks plus 10 new complexity-oriented tasks. It is a freeze candidate, not an untouched 30-task held-out test.

## Dataset integrity and expansion

The original pool remains 20/20 Base-Fail and 20/20 Gold-Pass. E1-B adds 10/10 Base-Fail and 10/10 Gold-Pass tasks. The 10 new tasks have unique source commits and zero source-commit overlap with the original pool.

Across the 30-task executable pool, the structural audit records 6 multi-file Gold tasks, 2 async-signal tasks, 5 state-signal tasks, 2 config-signal tasks, 2 hard-negative tasks, and 4 tasks with at least two PASS_TO_PASS nodes. Freeze-candidate hashes and identities are recorded in `evals/results/e1b_freeze_manifest.json`.

## Hardened frozen Stage-1 result

| Arm | Tasks | Oracle Pass@1 | SER | Avg calls | Avg tokens | Irrelevant-read ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fair V0 group-aware | 4 | 1.00 | 1.00 | 2.00 | 122.5 | 0.000 |
| V1 frozen | 4 | 1.00 | 1.00 | 1.25 | 87.0 | 0.125 |

Failure taxonomy for both arms: resolved=4, invalid_base=0, retrieval_blocked=0, patch_failure=0, regression_failure=0.

On this four-task frozen smoke, V1 preserves constrained Oracle editability while reducing average retrieval calls by 37.5% and average context tokens by 28.98%. V1 does not dominate every evidence-purity metric: mean irrelevant-read ratio is 12.5% versus 0% for V0 on these four tasks.

## Gold recall versus sufficient evidence

Gold-file recall and repair sufficiency are not equivalent. The sandbox-gc task resolves even though retrieval does not expose every file present in the full Gold patch. Full Gold-file recall is therefore not treated as a necessary condition for successful repair.

Sufficient Evidence Rate (SER) is the fraction of tasks the constrained Oracle Editor resolves under the files exposed by retrieval. On the current four-task smoke, SER is 1.00 for both arms.

Evaluation ladder:

`Gold Evidence Recall -> SER -> Oracle Pass@1 -> Autonomous Repair Rate`

The later Oracle-to-Autonomous difference is reported as Editor/Reasoning Gap rather than attributed to retrieval.

## Claim boundary

Supported: on the current four-task frozen smoke, V1 reduces calls and context tokens without reducing constrained Oracle editability.

Not supported: V1 improves autonomous patch success; the 30-task pool is an untouched held-out benchmark; the result generalizes across repositories; or n=4 establishes statistical significance.

## Next gate

Create a new explicit E1-B evaluation split/freeze before using the 30-task pool for Autonomous Editor comparison. Gold sources and labels must remain hidden from the Autonomous Editor. Oracle and Autonomous arms must use matched task, retrieval-evidence, and budget conditions, with Retrieval Gap, Editor/Reasoning Gap, and Regression Gap reported separately.
