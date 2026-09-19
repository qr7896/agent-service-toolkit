# V3 Experiment Checklist

## Before collection
- [ ] Use a real Git clone with readable HEAD; preflight must report `ready_to_collect=true`.
- [ ] Keep sealed TEST closed and select only non-sealed tasks.
- [ ] Create the cohort marker only from a passing preflight artifact.
- [ ] Preserve `v3-trajectory-v1`; never backfill historical execution provenance.

## During collection
- [ ] Treat the raw trajectory JSONL as immutable append-only evidence.
- [ ] Capture source repository and commit at execution time.
- [ ] Keep retrieved experience IDs distinct from adopted IDs.
- [ ] `adoption_observed=false` means adopted IDs are `null`; observed adoption must be a subset of retrieved IDs.
- [ ] Do not use future trajectories or same-time events as past evidence.
- [ ] Missing commit distance must abstain/fail closed.

## Evaluation
- [ ] Filter rows by cohort marker before readiness/replay.
- [ ] Verify strict past-only chronological replay and source-commit alias blocking.
- [ ] Keep positive, negative, and excluded experience outcomes distinct.
- [ ] Run matched memory arms from the same eligible past pool.
- [ ] Keep proxy/provider token costs separate.
- [ ] Never treat synthetic smoke artifacts as real prospective evidence.

## Reporting
- [ ] Report provenance completeness, ready/blocked rows, abstentions, adoption-observation coverage, matched counterfactual coverage, and independently graded outcomes.
- [ ] Preserve claim boundaries: readiness/replay connectivity is not evidence of efficacy or causality.
- [ ] Store derived artifacts separately from raw JSONL.
- [ ] Run artifact audit before using results in a paper, resume, or interview.


## Final artifact audit
Run `python -m evals.v3_audit --collection .codex/v3/cohort.json --status .codex/v3/status.json --frozen .codex/v3/frozen.json --output .codex/v3/audit.json`. Default mode rejects synthetic artifacts. `start` requires a passing `--preflight` artifact. The desktop workspace passed Git preflight on 2026-09-19; rerun it from a clean committed checkout immediately before cohort start.
