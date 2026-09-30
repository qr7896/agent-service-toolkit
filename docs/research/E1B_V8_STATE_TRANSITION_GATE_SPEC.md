# E1-B v8 State-Transition Preservation Gate — frozen offline candidate

Date: 2026-09-20
Schema: `e1b-state-transition-v1`

## Purpose

The gate is a deterministic necessary-condition check between participant coverage and patch application. It consumes only the public behavioral contract plus candidate replacement content. It never consumes tests, grader outcomes, gold patches, original TEST fixtures, or replacement held-out outcomes.

## Stable artifact schema

A transition contract contains:
- `schema_version`
- `target_obligations[] = {state, mode=change}`
- `preservation_obligations[] = {state, mode=identity}`
- `default_transition=identity`
- public-problem provenance.

An audit contains:
- `schema_version`
- ordered `obligations[]` with witness_count / guarded_witness / satisfied
- `missing_obligations[]`
- deterministic `truthiness_guards[]`
- `transition_witness_complete`
- explicit scope text.

Patch files are sorted before audit so mapping insertion order cannot change the artifact.

## Fail-closed conditions

The candidate fails this gate when:
1. an explicitly named target or preserved state/version has no guarded witness; or
2. the candidate contains a simple truthiness branch such as `if status:` / `if not status:`, because it can collapse distinct named states.

Bare literals do not satisfy an obligation. A nearby generic `if` keyword also does not count as an explicit comparison.

## Frozen interpretation boundary

PASS means only: every explicitly extracted obligation has a static guarded witness and no simple truthiness-collapse pattern was detected.

PASS does **not** prove:
- the guard is on the correct variable;
- the branch returns the correct value;
- all paths preserve identity;
- semantic equivalence;
- absence of destructive mutation;
- runtime correctness.

FAIL can be a false positive when equivalent behavior is implemented through helpers, tables, pattern abstractions, aliases, generated code, or another syntax not recognized by the conservative scanner.

PASS can be a false negative for real bugs when a syntactically guarded but semantically wrong branch satisfies the witness, when mutation happens outside the local window, or when the public statement does not explicitly name the relevant preserved state.

These limitations are part of the frozen candidate and must not be tuned using hidden outcomes.

## Frozen runner/result integration

Future v8 uses independent identity `e1b-r10-dev-v8`, ledger `.codex/e1b/r10-v8/provider_calls.jsonl`, result `evals/results/e1b_autonomous_dev_run_v8.json`, result schema `e1b-r10-v8-result-v1`, and transition schema `e1b-state-transition-v1`.

Both proposal and reviewed final patch must pass Coverage Gate first and State-Transition Gate second before `apply_patch` or grader execution. Coverage and transition failures are distinct (`contract_coverage_failure` vs `state_transition_failure`). Tasks with zero explicit transition obligations pass the transition gate vacuously unless an independently detected truthiness-collapse pattern is present. Proposal/final transition audit dictionaries are persisted in result rows.

`e1b_dev_v8_audit.py` verifies schema/gate enforcement, ledger call/token reconciliation, v7→v8 transitions, regressions, and the unchanged 4/4 freeze rule. It refuses to run before live artifacts exist.

## Live gate

No v8 live run is authorized. Before any future live call:
1. freeze runner integration and result schema;
2. zero-call preflight must pass;
3. preserve independent run id / ledger / result path;
4. keep the 4/4 DEV freeze rule;
5. do not open replacement held-out outcomes unless the predeclared DEV gate is met.
