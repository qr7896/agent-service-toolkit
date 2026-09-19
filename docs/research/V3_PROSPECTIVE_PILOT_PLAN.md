# V3 Non-sealed Prospective Pilot Plan

## Material Passport

- Status: PROPOSED / NOT STARTED
- Date: 2026-09-19
- Model/API calls in this planning step: 0
- Sealed TEST opened/called: 0/0
- Purpose: freeze a low-token pilot source, model identity, and budget before cohort start

## Recommended task source

Use three chronological **repository-local commit-replay development tasks** for the first pilot. Their commit IDs are not referenced by the current `evals/tasks`, `evals/results`, documentation, or `.codex` trajectory artifacts, and all three commits postdate the 2026-09-10 DeepSeek V4.1 Flash release.

| Order | Fix commit | Base commit | Development task |
|---|---|---|---|
| 1 | `9ffa8ad` | `6bef74819e1e161cb8957095c243949e3d17808f` | Make repository `evals` importable during pytest collection |
| 2 | `a1f4f78` | `9ffa8ad5f67dd88f72bfda12f357456a9bde9fd1` | Make research CLIs directly runnable without an import-path failure |
| 3 | `54242a0` | `4e71447cf8c51d5c7fee4ac872d6f7a0bbcf61ee` | Make frozen artifact hashes portable across newline conventions |

For each task, expose only the issue statement and base checkout to the agent. Keep the fix patch and grader assertions outside the agent workspace. These are non-sealed development tasks, not an external generalization benchmark; results may establish collection feasibility and chronological reuse evidence only.

## External follow-up sources

1. **SWE-smith train split** is the preferred second-stage source: it provides many public training tasks and multiple tasks per repository, which suits chronological experience transfer. It requires Docker and is officially developed/tested on Ubuntu, so it is not the lowest-cost Windows pilot.
2. **SWE-bench development tasks** are suitable for later real-issue validation, but the official harness recommends substantial storage and compute. Do not use SWE-bench Verified/test as the initial development stream.
3. Existing `research_v0`, `repo_tasks`, E1-B DEV, E1-B sealed TEST, and SERBench Test500 are excluded: the first three have prior project exposure and the latter two are protected evaluation material.

## Model freeze

- Provider: official DeepSeek API (`https://api.deepseek.com`)
- Canonical model ID: `deepseek-flash`
- Served model at freeze time: DeepSeek-V4.1-Flash
- Legacy `deepseek-v4-flash` is not used as the frozen ID because DeepSeek currently redirects that retired name to V4.1 Flash.
- Thinking: disabled for the pilot
- Temperature: `0`
- Record the response model identifier, usage fields, service fingerprint when available, prompt hash, and runner/config hash for every call.

## Conservative token budget

- Pilot size: **3 tasks**
- Global provider-reported total-token ceiling: **30,000 tokens**
- Admission reserve: **10,000 tokens per not-yet-started task**
- Maximum model calls: **4 per task**
- Maximum generated output: **600 tokens per call**
- Stop rule: after each atomic call, do not start another call or task if its full reserve no longer fits; never compensate by opening sealed tasks or silently increasing the ceiling.

This ceiling is intentionally a feasibility budget, not a power-analysis budget. Three tasks cannot support an efficacy or statistical-generalization claim. If any task consumes more than 10,000 tokens, stop the pilot and inspect the runner before requesting more budget.

## Gate before cohort start

The current normal Coding Agent runner does not yet enforce all limits above, and its DeepSeek enum still uses the retired alias. Before creating the cohort marker, add and test fail-closed call/output/admission limits, switch to the canonical model ID, build the three hidden graders, and rerun the V3 preflight on a clean HEAD.

## Sources

- DeepSeek API change log and model migration: <https://api-docs.deepseek.com/updates/>
- DeepSeek current model/pricing page: <https://api-docs.deepseek.com/quick_start/pricing/>
- SWE-smith official repository: <https://github.com/SWE-bench/SWE-smith>
- SWE-bench official dataset guide: <https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/datasets.md>
- SWE-bench official harness requirements: <https://github.com/SWE-bench/SWE-bench/blob/main/docs/reference/harness.md>
