# V3 Prospective Collection Runbook

This runbook starts a non-sealed prospective cohort without fabricating trajectories.

## 1. Preflight

```bash
python -m evals.v3_collection preflight --trajectories .codex/trajectories/coding_agent.jsonl --output .codex/v3/preflight.json
```

Proceed only when `ready_to_collect` is true. A missing Git repository/HEAD fails closed because execution provenance cannot be guaranteed.

## 2. Start cohort

Create the cohort marker immediately before the first real Coding Agent task:

```bash
python -m evals.v3_collection start --collection-id v3-prospective-001 --trajectories .codex/trajectories/coding_agent.jsonl --preflight .codex/v3/preflight.json --output .codex/v3/cohort.json
```

## 3. Run real non-sealed Coding Agent tasks

Use the normal application/runtime. Do not use sealed TEST tasks and do not backfill provenance into historical rows.

## 4. Check status

```bash
python -m evals.v3_collection status --manifest .codex/v3/cohort.json --output .codex/v3/status.json
```

Only rows ending on or after the cohort marker are counted.

## 5. Frozen evaluation

Once readiness and sample requirements are met, run the frozen chronological replay, memory ablation, and counterfactual-readiness tools. Derived artifacts must remain separate from the raw trajectory JSONL.


## Final artifact audit
Run `python -m evals.v3_audit --collection .codex/v3/cohort.json --status .codex/v3/status.json --frozen .codex/v3/frozen.json --output .codex/v3/audit.json`. Default mode rejects synthetic artifacts. `start` requires a passing `--preflight` artifact. The desktop workspace passed Git preflight on 2026-09-19; rerun it after committing the frozen mechanism and immediately before cohort start.
