# WebCodex test handoff — V3 compact pilot

Copy the prompt below into a WebCodex task connected to `qr7896/agent-service-toolkit` on branch `main`.

```text
Continue the test-and-fix phase for project20260827. Work only in the checked-out repository and follow the root AGENTS.md.

Goal:
Verify and, if necessary, minimally fix the V3 compact non-sealed pilot test path. This is test-only work. Do not start any real-model experiment.

Current verified local state before handoff:
- The earlier normal-agent pilot stopped at task 1 after 10,814 provider tokens and produced no patch.
- The replacement compact runner uses one exact-edit model call per non-sealed task, 4,000 tokens/task, 12,000 total, 600 output tokens/call, thinking disabled.
- Local focused regression: 10 passed.
- Local compact preflight: ready=true; all 3 tasks are Base-Fail + Gold-Pass.
- Conservative prompt reserves: task 1 = 1,488; task 2 = 2,792; task 3 = 2,432 tokens.
- No compact live-model call or new cohort marker has been created.

Hard boundaries:
1. Do not run `python -m evals.v3_compact_pilot run` or `python -m evals.v3_pilot_runner run`.
2. Do not access or run the six sealed E1-B TEST tasks, SERBench private certificates, or Test500.
3. Do not use DEEPSEEK_API_KEY or make any paid/provider model call.
4. Do not change the frozen V1 policy artifacts or reinterpret any test count as repair rate, patch success, or V3 efficacy.
5. You may edit production code and tests only when needed to fix a reproduced defect. Do not weaken assertions, delete tests, add blanket skips, or inflate timeouts just to get green output.

Environment setup:
1. Confirm Python is 3.12, 3.13, or 3.14.
2. Run: `uv sync --frozen --group dev`

Required focused checks, in order:
1. `uv run ruff check src/agents/model_budget.py evals/v3_pilot_runner.py evals/v3_compact_pilot.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py`
2. `uv run pytest -q tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py`
3. `uv run python -m evals.v3_compact_pilot preflight`

Expected compact preflight:
- ready=true
- each task: base_fails=true, gold_passes=true, reserve_fits=true
- prompt reserves remain <=4,000 per task

After focused checks, run:
4. `uv run pytest -q`

If anything fails:
- Reproduce the narrowest failing command first.
- Determine whether it is a real assertion/code defect, OS/path portability issue, dependency/setup issue, or timing-only failure.
- Apply the smallest root-cause fix.
- Rerun the narrow failure, then all three focused checks.
- Do not silently classify a failure as pre-existing; provide the exact error evidence.

Deliverable:
- Commit the minimal fixes on your task branch.
- Report commit SHA, exact commands, passed/failed/skipped counts, elapsed time, and changed files.
- State explicitly: real provider calls=0; sealed TEST opened/called=0/0.
- If the full suite still has failures, list each one with classification and evidence. Do not start the live compact pilot; return control to the user for explicit command approval.
```
