# Repository agent instructions

## Environment and tests

- Use Python 3.12–3.14 and the committed `uv.lock`.
- Install reproducibly with `uv sync --frozen --group dev`.
- Run focused checks before the full suite:
  - `uv run ruff check src/agents/model_budget.py evals/v3_pilot_runner.py evals/v3_compact_pilot.py tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py`
  - `uv run pytest -q tests/test_model_budget.py tests/test_v3_pilot_runner.py tests/test_v3_compact_pilot.py`
  - `uv run python -m evals.v3_compact_pilot preflight`
- Then run `uv run pytest -q`. Report environment/timeouts separately from assertion failures.

## Research safety boundary

- Do not run `evals.v3_pilot_runner run`, `evals.v3_compact_pilot run`, or any real-model experiment unless the user explicitly authorizes that exact command.
- Do not open or execute the six sealed E1-B TEST tasks or SERBench private/Test500 material.
- Do not add provider budget, retry a provider call, or use `DEEPSEEK_API_KEY` during test-only work.
- Never describe test counts as repair rate, patch success, or memory efficacy.

## Editing tests

- Tests may be fixed when the fixture, portability assumption, timeout, or expectation is demonstrably wrong.
- Do not weaken assertions, delete coverage, convert failures to skips, or increase timeouts merely to obtain green output.
- Make the smallest root-cause change and rerun the focused command that originally failed.
